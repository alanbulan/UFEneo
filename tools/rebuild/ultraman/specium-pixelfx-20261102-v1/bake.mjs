// 初代现装斯派修姆的纯表现升级；保持三个旧能量档，不能当成三种独立技能完成。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[at+1]);
if(!OUT.startsWith(ROOT+'\\')&&!OUT.startsWith(ROOT+'/'))throw Error('输出必须在工程内');
if(existsSync(join(OUT,'bundle.json')))throw Error('拒绝覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=661102;
const SHA=b=>createHash('sha256').update(b).digest('hex');
const PAL=fit(['#122f65','#1b539b','#3c8bb8','#71c8e3','#b7e7f2','#d6f6ff','#f0fcff','#ffffff'],8);
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function noise(x,salt){let k=Math.floor(x),u=x-k;u=u*u*(3-2*u);return hash(k+salt)*(1-u)+hash(k+1+salt)*u;}
function beam(p,t,spec){
 const envelope=t<3?[.65,.87,1][t]:t<spec.count-8?1:Math.max(.04,(spec.count-t)/8)**1.4;
 const radius=spec.radius,L=spec.length;
 for(let x=0;x<L;x++){
  const warp=(noise((x-t*16)/63,71)-.5)*37,center=(noise((x+warp-t*14)/39,431)-.5)*radius*.18;
  const edge=Math.min(1,(x+3)/14,(L-x)/16);
  const r=radius*(.77+.32*noise((x+warp-t*23)/19,997)+.16*noise((x+t*8)/7.3,1319))*edge;
  for(let y=-Math.ceil(radius*2.2);y<=Math.ceil(radius*2.2);y++){
   const q=Math.abs(y-center)/Math.max(.4,r);if(q>1.85)continue;
   const vein=noise((x+t*11+y*4)/11,1801);
   let level=q<.25?7:q<.49?6:q<.72?5:q<1?4:q<1.22?2:1;
   if(q>.3&&q<.8&&vein<.19)level=Math.max(2,level-2);
   let alpha=q<.72?1:q<1?.92:q<1.22?.60:(1.85-q)*.32;
   if(q>1.03&&noise((x-t*20)/4.1,2309)<.22)alpha*=.3;
   p.blend(x,y,PAL[level],alpha*envelope);
  }
  if(x%4===0)p.glow(x,center,5+r*.85,PAL[3],.09*envelope*edge);
 }
 // 边缘光屑有独立位置/寿命；不是把同一小片平铺或把I束放大。
 for(let j=0;j<67;j++){
  const age=t-(hash(j+3109)*(spec.count+5)-4);if(age<0||age>4.5)continue;
  const x=10+hash(j+4111)*(L-60)+age*(7+hash(j+5101)*12);if(x>L-8)continue;
  const sign=hash(j+6113)>.5?1:-1,y=sign*(radius*.9+age*.7),tail=5+hash(j+7103)*17,k=(1-age/4.5)*envelope;
  p.polyline([[x-tail,y*.7],[x-tail*.35,y+sign],[x,y]],PAL[4],k*.75);p.glow(x,y,3,PAL[2],k*.13);
 }
 p.glow(1,0,7+radius*.2,PAL[5],.35*envelope);p.disc(1,0,2.2,PAL[7],envelope);
}
const specs=[{level:1,length:420,count:32,size:[464,72],anchor:[16,36],radius:5.8},
 {level:2,length:420,count:32,size:[464,104],anchor:[16,52],radius:11.4},
 {level:3,length:680,count:48,size:[720,128],anchor:[16,64],radius:17.4}];
const bindings={},exports=[];
for(const spec of specs){
 const id='ultraman_specium_pixelfx_'+spec.level,folder=join(OUT,id);mkdirSync(folder);
 const [w,h]=spec.size,cols=4,rows=Math.ceil(spec.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4),rects=[],frames=[],hashes=[];
 for(let i=0;i<spec.count;i++){
  const frame=createFrame(w,h),p=painterFor(frame).place(...spec.anchor);beam(p,i,spec);
  const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);for(let j=0;j<rgba.length;j+=4)if(rgba[j+3]<3)rgba.fill(0,j,j+4);
  const x=i%cols*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,w,h]);
  frames.push({filename:String(i).padStart(2,'0')+'.png',frame:{x,y,w,h},rotated:false,trimmed:false,spriteSourceSize:{x:0,y:0,w,h},sourceSize:{w,h},duration:1000/60});
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 writeFileSync(join(folder,'aseprite.json'),JSON.stringify({frames,meta:{app:'https://github.com/patch-gg/pixelfx',image:'atlas.png',format:'RGBA8888',size:{w:w*cols,h:h*rows},scale:'1',pixelfx:{fps:60,pivot:spec.anchor,frameSize:spec.size,loop:false}}},null,2)+'\n');
 bindings[spec.length+':'+spec.level]={id,texture:`res://assets/effects/ultraman/specium-pixelfx-20261102-v1/${id}/atlas.png`,rects,anchor:spec.anchor,ticks:1,loop:false,display_scale:[1,1],visual_scale:1,full_frame:true,emission_anchor:true,source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',authoring_source:'res://tools/rebuild/ultraman/specium-pixelfx-20261102-v1/bake.mjs'};
 exports.push({...spec,id,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'bindings.json'),JSON.stringify(bindings,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.specium.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.map(s=>s.id)}));
