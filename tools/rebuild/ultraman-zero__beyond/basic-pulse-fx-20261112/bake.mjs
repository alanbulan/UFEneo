// PixelFX 离线烘焙：超限赛罗专属脉冲弹（正式 id zero_beyond_fx_pulse_flight / zero_beyond_fx_pulse_hit）。
// 形状由本文件绘制函数原创，不读他人特效图集；青蓝色板与形态一致。
// 每帧硬 Alpha、8 色板量化、4 邻域只留最大主体。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[at+1]);if(existsSync(join(OUT,'provenance.json')))throw Error('拒绝覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=112014;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
const TAU=Math.PI*2;
const CYAN=fit(['#041018','#0b2440','#104a6a','#1c6f96','#2f9cc4','#5fc4e8','#a8e4f8','#ffffff'],8);

function star(p,cx,cy,r,PAL,ph,spikes=4){
 const base=ph*TAU*0.25;
 for(let k=0;k<spikes;k++){
  const a=base+k*TAU/spikes;
  const len=r*(0.75+0.25*Math.sin(ph*TAU*3+k*1.7));
  p.line(cx,cy,cx+Math.cos(a)*len,cy+Math.sin(a)*len,(u)=>(u<0.45?PAL[7]:PAL[5]));
 }
 p.circle(cx,cy,r*0.22,PAL[6]);p.circle(cx,cy,r*0.12,PAL[7]);
}
function keepLargest(mask,w,h){
 const labels=new Int32Array(w*h).fill(-1);
 let bestId=-1,bestSize=0,id=0;
 const q=new Int32Array(w*h);
 for(let i=0;i<w*h;i++){
  if(!mask[i]||labels[i]>=0)continue;
  let head=0,tail=0,size=0;q[tail++]=i;labels[i]=id;
  while(head<tail){
   const p=q[head++],x=p%w,y=(p/w)|0;size++;
   if(x>0){const n=p-1;if(mask[n]&&labels[n]<0){labels[n]=id;q[tail++]=n;}}
   if(x+1<w){const n=p+1;if(mask[n]&&labels[n]<0){labels[n]=id;q[tail++]=n;}}
   if(y>0){const n=p-w;if(mask[n]&&labels[n]<0){labels[n]=id;q[tail++]=n;}}
   if(y+1<h){const n=p+w;if(mask[n]&&labels[n]<0){labels[n]=id;q[tail++]=n;}}
  }
  if(size>bestSize){bestSize=size;bestId=id;}id++;
 }
 if(bestId<0)return mask;
 const out=new Uint8Array(w*h);
 for(let i=0;i<w*h;i++)if(labels[i]===bestId)out[i]=1;
 return out;
}
function quantizeToPal(r,g,b,pal){
 let best=0,bestD=1e9;
 for(let k=0;k<pal.length;k++){
  const c=pal[k],pr=c&255,pg=(c>>>8)&255,pb=(c>>>16)&255;
  const dr=r-pr,dg=g-pg,db=b-pb,d=dr*dr+dg*dg+db*db;
  if(d<bestD){bestD=d;best=k;}
 }
 return pal[best];
}
// ---------- 飞行弹体：青蓝亮核 + 双环 + 四向短芒 + 后掠碎光 ----------
function pulseFlightBody(p,ph,PAL){
 const wob=1+0.08*Math.sin(ph*TAU*4);
 const R=33*wob;
 p.glow(0,0,R*1.9,PAL[4],0.28);
 p.ring(0,0,R*1.12,2,PAL[4],0.92);
 p.ring(0,0,R*0.86,2,PAL[5],0.95);
 p.ring(0,0,R*0.62,2,PAL[6],0.96);
 p.circle(0,0,R*0.46,PAL[6]);
 p.circle(0,0,R*0.28,PAL[7]);
 p.circle(0,0,R*0.13,PAL[7]);
 for(let k=0;k<4;k++){
  const a=ph*TAU*2+k*TAU/4;
  const len=R*(0.9+0.22*Math.sin(ph*TAU*3+k));
  p.line(Math.cos(a)*R*0.22,Math.sin(a)*R*0.22,Math.cos(a)*len,Math.sin(a)*len,(u)=>(u<0.4?PAL[7]:PAL[5]),(u)=>(u<0.6?1.05:1.45-u));
 }
 for(let j=0;j<4;j++){
  const a=Math.PI+(-0.45+j*0.3)+Math.sin(ph*TAU*2+j)*0.1;
  const d=R*(0.85+0.45*((j%3)/2));
  p.disc(Math.cos(a)*d,Math.sin(a)*d,1.1,j%2?PAL[6]:PAL[7],0.82);
 }
 star(p,0,0,R*0.34,PAL,ph,4);
}
// ---------- 命中爆：亮核 + 放射芒 + 扩散环 + 碎光 ----------
function pulseHitBody(p,ph,PAL){
 const k=1-ph;
 const R=54*(0.3+0.7*ph);
 p.circle(0,0,R*0.26*(0.7+0.3*k),PAL[7],0.95);
 p.circle(0,0,R*0.42,PAL[6],0.7*k+0.2);
 for(let i=0;i<10;i++){
  const a=i*TAU/10+ph*1.6;
  const len=R*(0.85+0.5*Math.sin(ph*TAU*4+i*1.2));
  p.line(0,0,Math.cos(a)*len,Math.sin(a)*len,(u)=>(u<0.35?PAL[7]:i%2?PAL[6]:PAL[5]),(u)=>(u<0.5?1.05:1.35-u));
 }
 for(let i=0;i<3;i++){
  const q=(((ph*1.5+i/3)%1)+1)%1;
  p.ring(0,0,2+R*0.8*q,Math.max(1,2.0*(1-q)),q<0.35?PAL[7]:PAL[5],(1.0-q)*k);
 }
 star(p,0,0,R*0.42,PAL,ph,4);
 for(let j=0;j<8;j++){
  const a=hash(j*11+3)*TAU,sp=14+hash(j*5+7)*28,d0=ph*sp;
  const x=Math.cos(a)*d0,y=Math.sin(a)*d0;
  if(k>0.12)p.disc(x,y,0.8+hash(j)*1.0,j%3?PAL[6]:PAL[7],k*0.82);
 }
 p.glow(0,0,R*0.85,PAL[5],0.4*k);
}

const SPECS={
 'zero_beyond_fx_pulse_flight':{n:4,W:96,H:96,AX:48,AY:48,loop:true,layer:'flight',draw:pulseFlightBody},
 'zero_beyond_fx_pulse_hit':{n:4,W:128,H:128,AX:64,AY:64,loop:false,layer:'impact',draw:pulseHitBody},
};
const exports=[];
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[],boxes=[];
 for(let i=0;i<spec.n;i++){
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  spec.draw(p,ph,CYAN);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  for(let j=0;j<rgba.length;j+=4){
   if(rgba[j+3]<4){rgba.fill(0,j,j+4);continue;}
   if(rgba[j+3]<128){rgba[j+3]=0;continue;}
   rgba[j+3]=255;
   const c=quantizeToPal(rgba[j],rgba[j+1],rgba[j+2],CYAN);
   rgba[j]=c&255;rgba[j+1]=(c>>>8)&255;rgba[j+2]=(c>>>16)&255;
  }
  // 4 邻域只留最大主体（alpha>=200 判 1）
  let mask=new Uint8Array(spec.W*spec.H);
  for(let q=0;q<spec.W*spec.H;q++)if(rgba[q*4+3]>=200)mask[q]=1;
  mask=keepLargest(mask,spec.W,spec.H);
  for(let q=0;q<spec.W*spec.H;q++)if(!mask[q]){const o=q*4;rgba[o]=rgba[o+1]=rgba[o+2]=rgba[o+3]=0;}
  // 逐帧 Alpha 外框（相对锚点）
  let x0=spec.W,y0=spec.H,x1=-1,y1=-1;
  for(let y=0;y<spec.H;y++)for(let x=0;x<spec.W;x++){
   if(rgba[(y*spec.W+x)*4+3]>0){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;}
  }
  boxes.push([x0-spec.AX,y0-spec.AY,x1-x0+1,y1-y0+1]);
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,kind:spec.layer,n:spec.n,W:spec.W,H:spec.H,AX:spec.AX,AY:spec.AY,loop:!!spec.loop,cols,rects,frame_boxes:boxes,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.zero-beyond-pulse.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length}));
