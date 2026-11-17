// Small physical-contact accents only. No actor, beam, charge or hitbox rendering.
// PixelFX MIT, Copyright (c) 2026 Patch and Hugo Duprez.
import {mkdirSync,existsSync,readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import {resolve,join,dirname,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {Rng} from '../../../../third_party/pixelfx/src/core/math.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要新 --out');
const OUT=resolve(ROOT,process.argv[at+1]);
const allowed=resolve(ROOT,'art/fighters/gomora/stage4/super2-palm-kick-pixelfx-v1');
const sub=relative(allowed,OUT);if(sub.startsWith('..')||isAbsolute(sub))throw Error('仅写本人新分支');
if(existsSync(join(OUT,'bundle.json')))throw Error('不覆盖冻结烘焙');
const H=b=>createHash('sha256').update(b).digest('hex');
const rel=p=>relative(ROOT,p).replaceAll('\\','/');
const upstream=JSON.parse(readFileSync(join(ROOT,'third_party/pixelfx/UPSTREAM.json'),'utf8'));
if(upstream.commit!=='a84159688af3ca37a4be05a0d422b94451b2e24e')throw Error('上游漂移');
const upstreamChecked=upstream.subset.map(r=>{
 const sha=H(readFileSync(join(ROOT,'third_party/pixelfx',r.path)));
 if(sha!==r.sha256)throw Error('上游源漂移 '+r.path);return {path:'third_party/pixelfx/'+r.path,sha256:sha};
});
mkdirSync(OUT,{recursive:true});
copyFileSync(join(ROOT,'third_party/pixelfx/LICENSE'),join(OUT,'LICENSE.pixelfx.txt'));
const PAL=fit(['#514537','#756347','#a58a5d','#c2ac7b','#d4c5a1'],5);

function palm(p,i){
 if(i===6)return;
 const age=i/60,fade=1-i/6,rng=new Rng(2026110211);
 // Compressed small contact plane then a few downward flecks. No ground dust cloud.
 if(i<2){p.line(-3-i,0,-1,1,PAL[3],fade);p.line(1,1,4+i,0,PAL[2],fade);}
 for(let k=0;k<10;k++){
  const side=k%2?-1:1,speed=rng.range(35,85),down=rng.range(15,65),life=rng.range(.055,.105);
  if(age>=life)continue;
  const x=side*(rng.range(0,2)+speed*age),y=rng.range(-1,2)+down*age+30*age*age;
  const len=i<3&&k%3===0?2:1;
  p.line(x,y,x+side*len,y+1,PAL[1+k%3],fade);
 }
}
function kick(p,i){
 if(i===6)return;
 const age=i/60,fade=1-i/6,rng=new Rng(2026110212);
 // Short forward pressure marks with irregular grains, not an energy projectile.
 if(i<2){p.line(-2,-3-i,0,-1,PAL[3],fade);p.line(0,1,-2,3+i,PAL[2],fade);}
 for(let k=0;k<12;k++){
  const speed=rng.range(45,140),dy=rng.range(-60,60),life=rng.range(.065,.12);
  if(age>=life)continue;
  const x=rng.range(0,2)+speed*age,y=rng.range(-2,2)+dy*age+25*age*age;
  const len=i<3&&k%3===0?3:1;
  p.line(x,y,x+len,y+dy/70,PAL[1+k%3],fade);
 }
}

const specs=[
 {id:'gomora_palm_kick_palm_contact',size:[48,40],anchor:[22,16],count:7,draw:palm,seed:2026110211,purpose:'掌group1真实hit肩背接触的小型压击碎点；不是强制弯身/抓取表现'},
 {id:'gomora_palm_kick_foot_contact',size:[56,40],anchor:[18,20],count:7,draw:kick,seed:2026110212,purpose:'足group2真实hit躯干接触的短促前向碎点；不是地面扬尘或弹体'},
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
  const png=encodePNG(w,h,rgba),path=join(folder,String(i).padStart(2,'0')+'.png');writeFileSync(path,png);
  frames.push({index:i,path:rel(path),rgba_sha256:H(rgba),png_sha256:H(png)});rects.push([x,y,w,h]);
 }
 const path=join(folder,'atlas.png'),png=encodePNG(w*cols,h*rows,atlas);writeFileSync(path,png);
 catalog[spec.id]={id:spec.id,atlas_candidate:rel(path),runtime_texture:null,rects,cell:spec.size,
  anchor:spec.anchor,anchor_space:'FX自身像素根；不是已量人物或世界接触点',ticks:1,loop:false,
  visual_scale:1,display_scale:[1,1],emission_anchor:true,source_kind:'pixelfx_code_baked',
  license:'MIT',upstream_commit:upstream.commit,attachment_status:'pending_new_actor_whole_frames',
  installed:false,purpose:spec.purpose};
 effects.push({id:spec.id,size:spec.size,anchor:spec.anchor,frames,atlas:rel(path),atlas_sha256:H(png),
  blank_last_frame:true,seed:spec.seed,purpose:spec.purpose});
}
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.gomora-palm-kick.v1',
 source:{path:rel(fileURLToPath(import.meta.url)),sha256:H(readFileSync(fileURLToPath(import.meta.url)))},
 upstream:'https://github.com/patch-gg/pixelfx/tree/'+upstream.commit,upstream_commit:upstream.commit,
 license:{path:rel(join(OUT,'LICENSE.pixelfx.txt')),sha256:H(readFileSync(join(OUT,'LICENSE.pixelfx.txt')))},
 upstream_checked:upstreamChecked,no_actor_or_rig_rendered:true,no_network:true,
 no_glow_beam_charge_or_large_explosion:true,whole_rgba_frames:true,installed:false,effects},null,2)+'\n');
console.log(JSON.stringify({output:OUT,effects:effects.map(e=>({id:e.id,phases:e.frames.length,atlas_sha256:e.atlas_sha256}))}));
