// UFEneo Gomora low-tail accents, offline whole RGBA frames only.
// PixelFX MIT, Copyright (c) 2026 Patch and Hugo Duprez.
// Locked upstream: a84159688af3ca37a4be05a0d422b94451b2e24e.
import {mkdirSync,existsSync,readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import {resolve,join,dirname,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {Rng} from '../../../../third_party/pixelfx/src/core/math.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要新 --out 目录');
const OUT=resolve(ROOT,process.argv[at+1]);
const allowed=resolve(ROOT,'art/fighters/gomora/stage4/super1-tail-sweep-pixelfx-v1');
const sub=relative(allowed,OUT);if(sub.startsWith('..')||isAbsolute(sub))throw Error('只可写本角色新候选分支');
if(existsSync(join(OUT,'bundle.json')))throw Error('不覆盖冻结烘焙');
const H=b=>createHash('sha256').update(b).digest('hex');
const rel=p=>relative(ROOT,p).replaceAll('\\','/');
const upstream=JSON.parse(readFileSync(join(ROOT,'third_party/pixelfx/UPSTREAM.json'),'utf8'));
if(upstream.commit!=='a84159688af3ca37a4be05a0d422b94451b2e24e')throw Error('PixelFX版本不符');
const upstreamChecked=upstream.subset.map(r=>{
 const sha=H(readFileSync(join(ROOT,'third_party/pixelfx',r.path)));
 if(sha!==r.sha256)throw Error(`PixelFX源漂移 ${r.path}`);return {path:`third_party/pixelfx/${r.path}`,sha256:sha};
});
mkdirSync(OUT,{recursive:true});
copyFileSync(join(ROOT,'third_party/pixelfx/LICENSE'),join(OUT,'LICENSE.pixelfx.txt'));
const DUST=fit(['#3f342b','#6c5740','#8f7353','#b0936d','#c7b18b','#d2c3a2'],6);
const GUARD=fit(['#4e5657','#7a8584','#a4b0aa','#c8cbb4','#ad916c'],5);

function wind(p,i){
 if(i===6)return;
 const fade=[.45,.75,.9,.72,.42,.18][i],u=i/5;
 // Small broken skimming wisps. No body, tail substitute, glow, ring or beam.
 for(let s=0;s<3;s++){
  const start=-15+s*12+u*16,length=22+s*5-u*8;
  let prev=null;
  for(let k=0;k<=Math.ceil(length);k++){
   const t=k/length,x=start+k,y=-2-s*4-Math.sin(Math.PI*t)*(2+s*.7)+u*3;
   if((k+s*3+i)%13>8){prev=null;continue;}
   if(prev)p.line(prev[0],prev[1],x,y,DUST[3+s%2],fade);
   else p.dot(x,y,DUST[3+s%2],fade);prev=[x,y];
  }
 }
 const rng=new Rng(2026110201);
 for(let k=0;k<7;k++){
  const x=rng.range(-13,35)+u*rng.range(12,26),y=2-u*rng.range(1,7);
  p.dot(x,y,DUST[2+k%3],fade*.7);
 }
}

function dust(p,i){
 if(i===9)return;
 const age=i/60,fade=Math.max(0,1-i/9),rng=new Rng(2026110202);
 for(let k=0;k<16;k++){
  const side=k%3===0?-1:1,speed=rng.range(50,155),lift=rng.range(45,125);
  const life=rng.range(.09,.17);if(age>=life)continue;
  const x=side*(rng.range(0,3)+speed*age),y=-2-lift*age+180*age*age;
  const size=i<3&&k%4===0?3:2,color=DUST[1+k%4];
  p.rect(x,y,size,size,color,fade*.85);
  if(i<4&&k%4===0)p.dot(x,y-1,DUST[5],fade*.6);
 }
 // A few irregular grains, no filled dust screen or impact star.
 if(i<3){p.line(-3-i,-1,-1-i,-2,DUST[3],fade);p.dot(4+i,-2,DUST[4],fade);}
}

function guard(p,i){
 if(i===7)return;
 const age=i/60,fade=1-i/7,rng=new Rng(2026110203);
 for(let k=0;k<12;k++){
  const a=Math.PI+rng.range(-1.05,1.05),speed=rng.range(40,120),life=rng.range(.07,.14);
  if(age>=life)continue;
  const x=Math.cos(a)*speed*age,y=Math.sin(a)*speed*age+40*age*age;
  const len=1+(k%3);
  p.line(x,y,x+Math.cos(a)*len,y+Math.sin(a)*len,GUARD[k%5],fade);
 }
 if(i<2){p.dot(1,-1,GUARD[3],fade);p.dot(-1,1,GUARD[2],fade);}
}

const specs=[
 {id:'gomora_tail_sweep_wind',size:[112,48],anchor:[24,24],count:7,draw:wind,purpose:'低尾横掠的短碎风线，仅表现；实际挂点待新03量取'},
 {id:'gomora_tail_sweep_hit_dust',size:[72,56],anchor:[28,42],count:10,draw:dust,purpose:'真实实体命中小尘，不在落空/防御伪播'},
 {id:'gomora_tail_sweep_guard_bits',size:[48,48],anchor:[28,24],count:8,draw:guard,purpose:'真实低防御接触的少量碎点，不画盾圈'},
];
const effects=[],catalog={};
for(const spec of specs){
 const [w,h]=spec.size,cols=4,rows=Math.ceil(spec.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4);
 const folder=join(OUT,spec.id);mkdirSync(folder,{recursive:true});
 const frames=[],rects=[];
 for(let i=0;i<spec.count;i++){
  const f=createFrame(w,h),p=painterFor(f).place(...spec.anchor);spec.draw(p,i);
  const rgba=composite(f,new Uint8ClampedArray(w*h*4),null);
  for(let q=0;q<rgba.length;q+=4)if(rgba[q+3]===0)rgba.fill(0,q,q+4);
  const x=i%cols*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba),path=join(folder,`${String(i).padStart(2,'0')}.png`);writeFileSync(path,png);
  frames.push({index:i,path:rel(path),rgba_sha256:H(rgba),png_sha256:H(png)});rects.push([x,y,w,h]);
 }
 const path=join(folder,'atlas.png'),png=encodePNG(w*cols,h*rows,atlas);writeFileSync(path,png);
 catalog[spec.id]={id:spec.id,atlas_candidate:rel(path),runtime_texture:null,rects,cell:spec.size,
  anchor:spec.anchor,anchor_space:'FX自身原生像素根，不是人物脚底或已量取尾段挂点',ticks:1,loop:false,
  visual_scale:1,display_scale:[1,1],emission_anchor:true,source_kind:'pixelfx_code_baked',
  license:'MIT',upstream_commit:upstream.commit,attachment_status:'pending_root_native_phase03_measurement',
  installed:false,purpose:spec.purpose};
 effects.push({id:spec.id,size:spec.size,anchor:spec.anchor,frames,atlas:rel(path),atlas_sha256:H(png),
  blank_last_frame:true,seed:2026110201+effects.length,purpose:spec.purpose});
}
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.gomora-low-tail.v1',
 source:{path:rel(fileURLToPath(import.meta.url)),sha256:H(readFileSync(fileURLToPath(import.meta.url)))},
 upstream:'https://github.com/patch-gg/pixelfx/tree/'+upstream.commit,upstream_commit:upstream.commit,
 license:{path:rel(join(OUT,'LICENSE.pixelfx.txt')),sha256:H(readFileSync(join(OUT,'LICENSE.pixelfx.txt')))},
 upstream_checked:upstreamChecked,no_actor_or_rig_rendered:true,no_network:true,
 no_glow_beam_charge_or_large_explosion:true,whole_rgba_frames:true,installed:false,effects},null,2)+'\n');
console.log(JSON.stringify({output:OUT,effects:effects.map(e=>({id:e.id,phases:e.frames.length,atlas_sha256:e.atlas_sha256}))}));
