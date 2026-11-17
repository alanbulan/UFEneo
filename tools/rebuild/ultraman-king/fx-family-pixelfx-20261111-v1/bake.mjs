// PixelFX离线烘焙：奥王专属特效家族（王者闪光红玛瑙束/洗礼红箭/再生蓝束/方向掌弹/金环贴掌双层）。
// 全部段真透明像素整帧；不借他人家族，不改人物与判定。照 fx-family（奥母）管线模式。
// 色板：红玛瑙（special/motion_236/623）、再生蓝白（special3）、金环（motion_214 贴掌光轮）。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {noiseFor} from '../../../../third_party/pixelfx/src/fx/fire/_lib.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[at+1]);if(existsSync(join(OUT,'provenance.json')))throw Error('拒绝覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711104;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function ease(v){return v*v*(3-2*v);}
const NOISE=noiseFor(.4);
const TAU=Math.PI*2;
// 色板（暗→亮）
const AGATE=fit(['#3d0d14','#7a1a20','#b82838','#e84a48','#f87868','#fca88c','#fed4b4','#ffffff'],8);  // 红玛瑙
const BLUE=fit(['#0a2440','#14406f','#2a6bb0','#4d96d8','#7ab8e8','#a8d4f4','#d4ecff','#ffffff'],8);    // 再生蓝白
const GOLD=fit(['#4d2a0a','#8f4d14','#cf7a2a','#e8a84d','#f2cd7a','#f9e4a8','#fcf2d4','#ffffff'],8);    // 金环

// ---------- 通用束体（照奥母家族） ----------
function beamBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const x=d;
  const w=thick*0.5*(1+0.10*Math.sin(d*0.32-ph*TAU*7))*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/14+0.25);
  const pulse=(((d*0.024-ph*3.4)%1)+1)%1<0.09?1:0;
  for(let q0=-w*1.35;q0<=w*1.35;q0+=0.5){
   const q=Math.abs(q0)/w,y=q0;
   let lv=q<0.18?7:q<0.38?6:q<0.6?5:q<0.82?4:q<1?3:2;
   lv=Math.max(2,lv-pulse);
   const edge=q>1&&(d*7%3<1);
   if(edge)continue;
   p.px(x,y,PAL[lv]);
  }
  for(let s=0;s<2;s++){
   const a=d*0.16-ph*TAU*5+s*Math.PI,off=Math.sin(a)*w*1.08;
   if(Math.cos(a)>-0.1)p.dot(x,off,Math.cos(a)>0.5?PAL[7]:PAL[6]);
  }
  if((Math.round(d*2)&7)===0)p.glow(x,0,w*2.4+4,PAL[5],0.16);
 }
 const fr=4.5+Math.sin(ph*TAU*9)*0.7;
 for(let i=0;i<4;i++){
  const a=ph*TAU*2.2+i*Math.PI/2,l=7+3*Math.sin(ph*TAU*6+i);
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?PAL[7]:PAL[6]));
 }
 p.circle(0,0,fr+1.4,PAL[5]);p.circle(0,0,fr,PAL[6]);p.circle(0,0,fr*0.55,PAL[7]);
 p.glow(0,0,30,PAL[6],0.75);
 const ir=4.5+Math.sin(ph*TAU*11)*0.7;
 for(let i=0;i<6;i++){
  const a=Math.PI+(i-2.5)*0.42,l=6+7*Math.abs(NOISE(ph,4,SEED*7+i));
  p.line(len,0,len+Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.4?PAL[7]:PAL[5]));
 }
 for(let k=0;k<2;k++){
  const q=(((ph*2.6+k/2)%1)+1)%1;
  p.ring(len,0,3+11*ease(q),Math.max(1,2*(1-q)),q<0.3?PAL[7]:PAL[5],1.05-q);
 }
 p.circle(len,0,ir+1.2,PAL[4]);p.circle(len,0,ir,PAL[6]);p.circle(len,0,ir*0.5,PAL[7]);
 p.glow(len,0,34,PAL[5],0.8);p.glow(len,0,10,PAL[7],0.5);
}
// ---------- 玛瑙束：主干带玛瑙棱面（内部多面折光块），端部棱斑 ----------
function agateBeamBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const x=d;
  const w=thick*0.5*(1+0.08*Math.sin(d*0.26-ph*TAU*5))*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/14+0.3);
  for(let q0=-w*1.3;q0<=w*1.3;q0+=0.5){
   const q=Math.abs(q0)/w,y=q0;
   let lv=q<0.18?7:q<0.4?6:q<0.62?5:q<0.85?4:3;
   // 玛瑙棱面: 纵向棱块交替明暗
   const facet=Math.sin(d*0.11+q0*0.35+ph*1.6)>0?0:-1;
   lv=Math.max(2,lv+facet);
   p.px(x,y,PAL[lv]);
  }
  for(let s=0;s<2;s++){
   const a=d*0.14-ph*TAU*4+s*Math.PI,off=Math.sin(a)*w*1.05;
   if(Math.cos(a)>-0.1)p.dot(x,off,Math.cos(a)>0.5?PAL[7]:PAL[6]);
  }
  if((Math.round(d*2)&7)===0)p.glow(x,0,w*2.3+4,PAL[5],0.15);
 }
 const fr=4.5+Math.sin(ph*TAU*9)*0.7;
 for(let i=0;i<4;i++){
  const a=ph*TAU*2.2+i*Math.PI/2,l=7+3*Math.sin(ph*TAU*6+i);
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?PAL[7]:PAL[6]));
 }
 p.circle(0,0,fr+1.4,PAL[5]);p.circle(0,0,fr,PAL[6]);p.circle(0,0,fr*0.55,PAL[7]);
 p.glow(0,0,30,PAL[6],0.75);
 const ir=4.5+Math.sin(ph*TAU*11)*0.7;
 for(let i=0;i<6;i++){
  const a=Math.PI+(i-2.5)*0.42,l=6+7*Math.abs(NOISE(ph,4,SEED*7+i));
  p.line(len,0,len+Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.4?PAL[7]:PAL[5]));
 }
 for(let k=0;k<2;k++){
  const q=(((ph*2.6+k/2)%1)+1)%1;
  p.ring(len,0,3+11*ease(q),Math.max(1,2*(1-q)),q<0.3?PAL[7]:PAL[5],1.05-q);
 }
 p.circle(len,0,ir+1.2,PAL[4]);p.circle(len,0,ir,PAL[6]);p.circle(len,0,ir*0.5,PAL[7]);
 p.glow(len,0,34,PAL[5],0.8);
}
// ---------- 通用飞行弹（照奥母家族） ----------
function boltBody(p,L,PAL,ph){
 const HEAD=5;
 for(let d=0;d<=L;d+=0.5){
  const u=d/L, x=-d;
  const w=(2.6*Math.pow(1-u,0.85)+0.5)*(d<HEAD?Math.sqrt(Math.max(0,1-((HEAD-d)/HEAD)**2)):1);
  const v0=Math.sin(d*0.7-ph*TAU*3)*0.5;
  for(let q0=-w*1.3;q0<=w*1.3;q0+=0.5){
   const q=Math.abs(q0)/w,y=q0+v0*u;
   const lv=q<0.2?7:q<0.42?6:q<0.66?5:q<0.9?4:3;
   p.px(x,y,PAL[lv]);
  }
 }
 for(const s of [0,Math.PI]){
  for(let d=1.5;d<L*0.72;d+=1){
   const a=d*0.42-ph*TAU*2.6+s,y=Math.sin(a)*(1.9*(1-d/L)+0.5);
   if(Math.cos(a)>0.25)p.dot(-d,y,Math.cos(a)>0.75?PAL[7]:PAL[6]);
  }
 }
 p.circle(0,0,2.6,PAL[6]);p.circle(-1,0,1.5,PAL[7]);
 p.glow(0,0,15,PAL[5],0.5);p.glow(-L*0.5,0,10,PAL[4],0.22);
}
// ---------- 能量箭：洗礼光线红色箭形（箭头+细杆+尾羽光） ----------
function arrowBody(p,L,PAL,ph){
 // 箭头: 实心三角
 for(let d=0;d<7;d+=0.5){
  const w=(d/7)*4.5;
  for(let q0=-w;q0<=w;q0+=0.5)p.px(d,q0,PAL[d<3?7:6]);
 }
 // 箭杆: 细亮芯+暗边
 for(let d=7;d<=L;d+=0.5){
  const u=d/L;
  const w=1.6*(1-u*0.3)+0.4;
  const shimmer=Math.sin(d*0.5-ph*TAU*4)*0.3;
  for(let q0=-w;q0<=w;q0+=0.5){
   const q=Math.abs(q0)/w;
   p.px(-d+7,shimmer+q0,PAL[q<0.5?7:q<1?5:3]);
  }
 }
 // 尾羽: 两撇斜光
 p.line(-L+7,-1,-L+1,-5,PAL[6]);p.line(-L+7,1,-L+1,5,PAL[6]);
 p.dot(-L+2,-4,PAL[7]);p.dot(-L+2,4,PAL[7]);
 // 微光晕
 p.glow(3,0,10,PAL[6],0.4);p.glow(-L*0.45,0,8,PAL[5],0.2);
}
// ---------- 通用命中爆（照奥母家族） ----------
function hitBurst(p,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12), k=1-ph;
 const R0=R*0.42*grow;
 for(let i=0;i<8;i++){
  const a=i*TAU/8+ph*2.4,l=R0*(1.5+0.7*Math.sin(ph*TAU*5+i*1.7));
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.45?PAL[7]:i%2?PAL[6]:PAL[5]),(u)=>(u<0.5?1:1.5-u));
 }
 p.circle(0,0,R0*1.3,PAL[4],k);p.circle(0,0,R0,PAL[6],k);p.circle(0,0,R0*0.55,PAL[7],k);
 for(let i=0;i<3;i++){
  const q=(((ph*1.8+i/3)%1)+1)%1;
  p.ring(0,0,3+R*0.5*ease(q),Math.max(1,2.2*(1-q)),q<0.3?PAL[7]:PAL[5],(1.1-q)*k);
 }
 p.glow(0,0,R*0.8,PAL[5],0.7*k);p.glow(0,0,R*0.3,PAL[7],0.5*k);
 for(let j=0;j<10;j++){
  const a=hash(j*3+1)*TAU,sp=30+hash(j*7+2)*60,d0=ph*sp;
  const x=Math.cos(a)*d0,y=Math.sin(a)*d0-d0*d0*0.05;
  const kk=1-ph;
  if(kk>0.15)p.disc(x,y,0.8+hash(j)*1.2,j%3?PAL[6]:PAL[7],kk*0.85);
 }
}
// ---------- 通用拖尾（照奥母家族） ----------
function trailBody(p,ph,PAL){
 for(let d=0;d<120;d+=1){
  const u=d/120,x=-d,y=Math.sin(d*0.22-ph*TAU*2.2)*3.2*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*8))%3)<2)p.px(x,y,PAL[lv]);
  if(d%9===0)p.glow(x,y,3,PAL[5],0.12*(1-u));
 }
 p.glow(0,0,12,PAL[6],0.35);
}
// ---------- 金环：贴掌光轮（双层 front/back 各画完整环，front 亮、back 暗） ----------
function ringForm(p,PAL,ph,bright){
 // 光轮在人物掌前成型: 环带渐显+旋绕流光
 const R=17;
 const form=0.35+0.65*ph;                    // 成型度
 for(let a=0;a<TAU;a+=0.045){
  // 环带: 外缘亮内缘暗
  for(let r=R-2.2;r<=R;r+=0.5){
   const x=Math.cos(a)*r,y=Math.sin(a)*r*0.96;
   const u=(r-(R-2.2))/2.2;
   const lv=bright?(u>0.7?7:u>0.4?6:4):(u>0.6?5:3);
   const tw=bright?(0.75+0.25*Math.sin(a*3+ph*TAU*2)):(0.55+0.2*Math.sin(a*3+ph*TAU*2+1.4));
   p.px(x,y,GOLD[lv],tw*form);
  }
 }
 // 旋绕流光: 沿环 2 段亮弧
 for(let k=0;k<2;k++){
  const a0=ph*TAU+k*Math.PI;
  for(let u=0;u<0.22;u+=0.02){
   const a=a0+u*TAU;
   const r=R-1+0.8*Math.sin(a*5+ph*8);
   const x=Math.cos(a)*r,y=Math.sin(a)*r*0.96;
   const head=1-u/0.22;
   if(bright){p.disc(x,y,1.2+head,GOLD[7],form*head);}
   else{p.disc(x,y,1+head*0.8,GOLD[6],form*head*0.85);}
  }
 }
 // 成型期边缘粒子
 for(let j=0;j<5;j++){
  const a=hash(j*7+3)*TAU+ph*1.8,d=(1-ph)*8+R+2;
  p.disc(Math.cos(a)*d,Math.sin(a)*d*0.9,0.9,GOLD[bright?7:5],(1-ph)*0.5*(bright?0.9:0.6));
 }
 p.glow(0,0,R*2.4,bright?GOLD[6]:GOLD[4],(bright?0.5:0.3)*form);
}

// ---------- 段规格 ----------
const SPECS={
 // 王者闪光(红玛瑙束): start 4帧 88x88 双臂水平前伸聚能 | beam 4帧 520x80 玛瑙棱面束 | hit 4帧 136x136
 'king_fx_flash_start':{n:4,W:88,H:88,AX:44,AY:44,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 双臂前伸: 两道对向棱光向中心汇聚
   for(let s=-1;s<=1;s+=2){
    for(let u=0;u<1;u+=0.05){
     const x=s*(28-u*24*k);
     const lv=u>0.7?6:4;
     p.disc(x,Math.sin(u*6-ph*TAU*3+s)*1.5,1.1+k*0.8,AGATE[lv],(0.5+0.5*k)*Math.min(1,u*2.4+0.25));
    }
   }
   // 玛瑙核: 多面折光圆
   p.circle(0,0,12*k+4,AGATE[4],0.85*k);p.circle(0,0,8.5*k+2,AGATE[6],k);p.circle(0,0,4*k,AGATE[7],k);
   for(let i=0;i<3;i++){const a=i*TAU/3+ph*2,l=8*k+3;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?AGATE[7]:AGATE[5]));}
   p.glow(0,0,32*k+10,AGATE[5],0.6*k);
 }},
 'king_fx_flash_beam':{n:4,W:520,H:80,AX:36,AY:40,loop:true,draw:(p,ph,t,W,H,AX,AY)=>agateBeamBody(p,476,32,AGATE,ph)},
 'king_fx_flash_hit':{n:4,W:136,H:136,AX:68,AY:68,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,56,AGATE,ph,0.36)},
 // 洗礼光线(红能量箭): start 4帧 80x80 胸前红宝玉聚能 | flight 4帧 96x48 箭形 | trail 4帧 160x48 | hit 4帧 120x120
 'king_fx_baptism_start':{n:4,W:80,H:80,AX:40,AY:40,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 胸前宝玉: 圆核渐亮+环绕收束光
   for(let i=0;i<3;i++){
    const q=(((ph*0.9+i/3)%1)+1)%1;
    p.ring(0,0,14-8*i,1.4,q<0.3?AGATE[7]:AGATE[5],(0.95-q*0.4)*k);
   }
   p.circle(0,0,11*k+3,AGATE[4],0.85*k);p.circle(0,0,7.5*k+2,AGATE[6],k);p.circle(0,0,3.6*k,AGATE[7],k);
   p.glow(0,0,28*k+8,AGATE[5],0.6*k);
 }},
 'king_fx_baptism_flight':{n:4,W:96,H:48,AX:70,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>arrowBody(p,56,AGATE,ph)},
 'king_fx_baptism_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,AGATE)},
 'king_fx_baptism_hit':{n:4,W:120,H:120,AX:60,AY:60,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,42,AGATE,ph,0.36)},
 // 王者再生光线(蓝白束): start 4帧 96x96 双臂交叉聚能 | beam 4帧 720x128 最大蓝束 | hit 4帧 144x144
 'king_fx_rebirth_start':{n:4,W:96,H:96,AX:48,AY:48,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 双臂交叉: 交叉光芒渐亮
   for(let s=0;s<2;s++){
    const a=(s?0.6:-0.6)+ph*1.1,l=22*k+7;
    p.line(-Math.cos(a)*l,-Math.sin(a)*l,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?BLUE[7]:BLUE[5]),(u)=>(u<0.6?1:1.5-u));
   }
   p.circle(0,0,13*k+4,BLUE[4],0.85*k);p.circle(0,0,9*k+2,BLUE[6],k);p.circle(0,0,4.2*k,BLUE[7],k);
   p.glow(0,0,34*k+10,BLUE[5],0.6*k);
 }},
 'king_fx_rebirth_beam':{n:4,W:720,H:128,AX:40,AY:64,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,668,52,BLUE,ph)},
 'king_fx_rebirth_hit':{n:4,W:144,H:144,AX:72,AY:72,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,60,BLUE,ph,0.36)},
 // 方向掌弹(红): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 4帧 112x112
 'king_fx_palm_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.4+0.6*ph;
   p.circle(0,0,9*k+3,AGATE[5],0.85*k);p.circle(0,0,5.5*k+1.5,AGATE[7],k);
   p.glow(0,0,24*k+8,AGATE[5],0.55*k);
   for(let j=0;j<3;j++){const a=hash(j*5+3)*TAU+ph*2.8,l=7*k+2;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,AGATE[j%2?7:6]);}
 }},
 'king_fx_palm_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,42,AGATE,ph)},
 'king_fx_palm_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,AGATE)},
 'king_fx_palm_hit':{n:4,W:112,H:112,AX:56,AY:56,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,38,AGATE,ph,0.36)},
 // 金环贴掌(光轮): form_back 4帧 128x128 暗层 behind | form_front 4帧 128x128 亮层
 'king_fx_ring_form_back':{n:4,W:128,H:128,AX:64,AY:64,behind:true,draw:(p,ph,t,W,H,AX,AY)=>ringForm(p,GOLD,ph,false)},
 'king_fx_ring_form_front':{n:4,W:128,H:128,AX:64,AY:64,draw:(p,ph,t,W,H,AX,AY)=>ringForm(p,GOLD,ph,true)},
};
// ---------- 烘焙循环 ----------
const exports=[],bindings={};
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];
 for(let i=0;i<spec.n;i++){
  const t=i/60;
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  spec.draw(p,ph,t,spec.W,spec.H,spec.AX,spec.AY);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  for(let j=0;j<rgba.length;j+=4)if(rgba[j+3]<4)rgba.fill(0,j,j+4);
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 bindings[id]={id,texture:`res://assets/effects/ultraman-king/fx-family-pixelfx-20261111-v1/${id}/atlas.png`,rects,
  anchor:[spec.AX,spec.AY],ticks:4,display_scale:[1,1],behind_fighter:!!spec.behind,full_frame:true,
  source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',
  authoring_source:'res://tools/rebuild/ultraman-king/fx-family-pixelfx-20261111-v1/bake.mjs'};
 if(spec.loop)bindings[id].loop=true;
 exports.push({id,n:spec.n,W:spec.W,H:spec.H,anchor:[spec.AX,spec.AY],behind:!!spec.behind,loop:!!spec.loop,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.king-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:Object.keys(bindings).length}));
