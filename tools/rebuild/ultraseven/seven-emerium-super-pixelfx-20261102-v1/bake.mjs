// 三级额灯束：PixelFX离线RGBA整相，原生680跨度；不调用人物/骨架/stockActor。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');
if(at<0)throw Error('需要 --out 新目录');
const OUT=resolve(ROOT,process.argv[at+1]);
if(!OUT.startsWith(ROOT+'\\')&&!OUT.startsWith(ROOT+'/'))throw Error('输出必须在工程内');
if(existsSync(join(OUT,'bundle.json')))throw Error('拒绝覆盖冻结候选');
mkdirSync(OUT,{recursive:true});
const SHA=b=>createHash('sha256').update(b).digest('hex');
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e';
const PAL=fit(['#064d41','#087652','#0db878','#3ae397','#83ffc1','#bcffdd','#e8fff1','#ffffff'],8);
const SIZE=[720,96],ANCHOR=[16,48],LENGTH=680,SEED=711102;
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function noise(x,salt){const k=Math.floor(x);let u=x-k;u=u*u*(3-2*u);return hash(k+salt)*(1-u)+hash(k+1+salt)*u;}
function field(x,t){
 const warp=(noise((x-t*14)/67,73)-.5)*49;
 return {center:(noise((x+warp-t*12)/47,307)-.5)*3.2,
  radius:9.2+4.8*noise((x+warp-t*19)/23,911)+2.7*noise((x+warp+t*7)/9.1,1249),
  rough:noise((x-t*23)/4.9,1709)};
}
function strength(t){return t<3?[.48,.76,.93][t]:t<40?1:t<48?[.94,.86,.75,.61,.46,.31,.19,.09][t-40]:0;}
function beam(p,t,k,after=false){
 for(let x=0;x<LENGTH;x++){
  const f=field(x,t),entrance=Math.min(1,(x+4)/18),tip=Math.min(1,(LENGTH-x)/18);
  const pressure=.5+.5*noise((x-t*29)/43,2129),r=f.radius*entrance*tip;
  for(let y=-31;y<=31;y++){
   const q=Math.abs(y-f.center)/Math.max(.5,r);
   if(q>1.9)continue;
   const vein=noise((x+t*7+y*3)/8,2207);
   let level=q<.22?7:q<.45?6:q<.68?5:q<.92?4:q<1.18?2:1;
   if(q>.38&&q<.82&&vein<.22)level=Math.max(2,level-2);
   let alpha=q<=.68?1:q<=.92?.96:q<=1.18?.64:(1.9-q)*.35;
   if(q>1.05&&f.rough<.29)alpha*=.31;
   if(after){level=Math.min(level,4);alpha*=.43;}
   p.blend(x,y,PAL[level],alpha*k);
  }
  if(x%4===0)p.glow(x,f.center,8+r*.72,PAL[3],.09*k*entrance*tip*pressure);
 }
 // 非等距的短羽流随时间向前传输，各自有限寿命；没有短裁片重复或圆环。
 for(let j=0;j<83;j++){
  const born=hash(j+3001)*53-5,age=t-born;
  if(age<0||age>5.5)continue;
  const x=12+hash(j+4001)*615+age*(6+hash(j+5001)*13);
  if(x>670)continue;
  const side=hash(j+6001)>.5?1:-1,fade=(1-age/5.5)*k;
  const y=side*(field(x,t).radius-1+age*.9),tail=6+hash(j+7001)*18;
  p.polyline([[x-tail,y*.65],[x-tail*.35,y+side*2],[x,y],[x+3,y*.76]],PAL[4],fade*.65);
  p.glow(x,y,3.5,PAL[2],fade*.16);
 }
 if(!after){p.glow(1,0,12,PAL[4],.46*k);p.disc(1,0,3.1,PAL[6],.9*k);p.disc(1,0,1.6,PAL[7],k);}
}
const specs=[
 {id:'seven_fx_emerium',count:48,expiry_ticks:48,expiry_effect:'seven_emerium_super_pixelfx_end',draw:(p,t)=>beam(p,t,strength(t))},
 {id:'seven_emerium_super_pixelfx_end',count:6,draw:(p,t)=>{if(t<5)beam(p,t+48,[.12,.09,.065,.045,.03][t],true);}}
];
const catalog={},exports=[];
for(const spec of specs){
 const [w,h]=SIZE,cols=4,rows=Math.ceil(spec.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4);
 const folder=join(OUT,spec.id);mkdirSync(folder,{recursive:true});
 const rects=[],frames=[],phaseHashes=[],pngHashes=[];
 for(let i=0;i<spec.count;i++){
  const frame=createFrame(w,h),p=painterFor(frame).place(...ANCHOR);spec.draw(p,i);
  const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);
  for(let j=0;j<rgba.length;j+=4)if(rgba[j+3]<3)rgba.fill(0,j,j+4);
  const x=(i%cols)*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba),name=String(i).padStart(2,'0')+'.png';
  writeFileSync(join(folder,name),png);phaseHashes.push(SHA(rgba));pngHashes.push(SHA(png));rects.push([x,y,w,h]);
  frames.push({filename:name,frame:{x,y,w,h},rotated:false,trimmed:false,spriteSourceSize:{x:0,y:0,w,h},sourceSize:{w,h},duration:1000/60});
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 writeFileSync(join(folder,'aseprite.json'),JSON.stringify({frames,meta:{app:'https://github.com/patch-gg/pixelfx',image:'atlas.png',format:'RGBA8888',size:{w:w*cols,h:h*rows},scale:'1',frameTags:[{name:spec.id,from:0,to:spec.count-1,direction:'forward'}],pixelfx:{fps:60,loop:false,pivot:ANCHOR,frames:spec.count,frameSize:SIZE}}},null,2)+'\n');
 catalog[spec.id]={id:spec.id,texture:`res://assets/effects/ultraseven/seven-emerium-super-pixelfx-20261102-v1/${spec.id}/atlas.png`,rects,anchor:ANCHOR,ticks:1,loop:false,display_scale:[1,1],visual_scale:1,full_frame:true,emission_anchor:true,source_kind:'pixelfx_code_baked',license:'MIT',upstream_commit:UPSTREAM,authoring_source:'res://tools/rebuild/ultraseven/seven-emerium-super-pixelfx-20261102-v1/bake.mjs',...(spec.expiry_ticks?{expiry_ticks:spec.expiry_ticks,expiry_effect:spec.expiry_effect}:{})};
 exports.push({id:spec.id,phases:spec.count,phase_rgba_sha256:phaseHashes,phase_png_sha256:pngHashes,atlas_sha256:SHA(png),rgba_straight_alpha:true});
}
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.bake.v1',art_source:'code',route:'PixelFX offline',seed:SEED,length:LENGTH,canvas:SIZE,anchor:ANCHOR,upstream_commit:UPSTREAM,source_sha256:SHA(readFileSync(SELF)),license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,exports},null,2)+'\n');
console.log(JSON.stringify({output:OUT,exports:exports.map(e=>({id:e.id,phases:e.phases}))}));
