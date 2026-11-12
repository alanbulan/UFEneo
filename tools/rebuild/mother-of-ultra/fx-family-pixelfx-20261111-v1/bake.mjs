// PixelFX离线烘焙：奥母专属特效家族（母亲光线/破坏光线/方向光弹/淋浴光雨/掌部充能）。
// 全部段真透明像素整帧；不借他人家族，不改人物与判定。照 q-outline 管线模式。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711105;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function ease(v){return v*v*(3-2*v);}
const NOISE=noiseFor(.4);
const TAU=Math.PI*2;
// 色板（暗→亮）
const HEAL=fit(['#0a2440','#14406f','#2a6bb0','#4d96d8','#7ab8e8','#a8d4f4','#d4ecff','#ffffff'],8);      // 母亲光线蓝白
const DEST=fit(['#3d0d14','#7a1a20','#b83a28','#e86438','#f79a4d','#fac87e','#fce8c4','#ffffff'],8);      // 破坏光线红金
const RAY=HEAL;                                                                                            // 方向光弹同母亲光色
const RAIN=fit(['#12324f','#1e5c8a','#3a8cc4','#66b4e4','#96d4f2','#c4ecf9','#e8f8ff','#ffffff'],8);       // 光雨冰蓝
const PALM=DEST;                                                                                           // 掌部充能红金

// ---------- 通用束体绘制：白热芯带横向脉动、缠绕光丝、端部辉光 ----------
function beamBody(p,W,H,AX,AY,len,thick,PAL,ph){
 const HY=AY; // 束中心线
 for(let d=0;d<=len;d+=0.5){
  const x=AX+d;
  const w=thick*0.5*(1+0.10*Math.sin(d*0.32-ph*TAU*7))*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/14+0.25);
  const pulse=(((d*0.024-ph*3.4)%1)+1)%1<0.09?1:0;
  for(let q0=-w*1.35;q0<=w*1.35;q0+=0.5){
   const q=Math.abs(q0)/w,y=HY+q0;
   let lv=q<0.18?7:q<0.38?6:q<0.6?5:q<0.82?4:q<1?3:2;
   lv=Math.max(2,lv-pulse);
   const edge=q>1&&(d*7%3<1);
   if(edge)continue;
   p.px(x,y,PAL[lv]);
  }
  // 双股缠绕光丝
  for(let s=0;s<2;s++){
   const a=d*0.16-ph*TAU*5+s*Math.PI,off=Math.sin(a)*w*1.08;
   if(Math.cos(a)>-0.1)p.dot(x,HY+off,Math.cos(a)>0.5?PAL[7]:PAL[6]);
  }
  if((Math.round(d*2)&7)===0)p.glow(x,HY,w*2.4+4,PAL[5],0.16);
 }
 // 发射端: 旋转光芒+白热圆芯
 const fr=4.5+Math.sin(ph*TAU*9)*0.7;
 for(let i=0;i<4;i++){
  const a=ph*TAU*2.2+i*Math.PI/2,l=7+3*Math.sin(ph*TAU*6+i);
  p.line(AX,HY,AX+Math.cos(a)*l,HY+Math.sin(a)*l,(u)=>(u<0.5?PAL[7]:PAL[6]));
 }
 p.circle(AX,HY,fr+1.4,PAL[5]);p.circle(AX,HY,fr,PAL[6]);p.circle(AX,HY,fr*0.55,PAL[7]);
 p.glow(AX,HY,30,PAL[6],0.75);
 // 端部: 热斑+外扩环
 const ir=4.5+Math.sin(ph*TAU*11)*0.7;
 for(let i=0;i<6;i++){
  const a=Math.PI+(i-2.5)*0.42,l=6+7*Math.abs(NOISE(ph,4,SEED*7+i));
  p.line(AX+len,HY,AX+len+Math.cos(a)*l,HY+Math.sin(a)*l,(u)=>(u<0.4?PAL[7]:PAL[5]));
 }
 for(let k=0;k<2;k++){
  const q=(((ph*2.6+k/2)%1)+1)%1;
  p.ring(AX+len,HY,3+11*ease(q),Math.max(1,2*(1-q)),q<0.3?PAL[7]:PAL[5],1.05-q);
 }
 p.circle(AX+len,HY,ir+1.2,PAL[4]);p.circle(AX+len,HY,ir,PAL[6]);p.circle(AX+len,HY,ir*0.5,PAL[7]);
 p.glow(AX+len,HY,34,PAL[5],0.8);p.glow(AX+len,HY,10,PAL[7],0.5);
}
// ---------- 通用飞行弹：白热圆头+带状尾锥+缠绕火星 ----------
function boltBody(p,AX,AY,L,PAL,ph){
 const HEAD=5;
 for(let d=0;d<=L;d+=0.5){
  const u=d/L, x=AX-d;
  const w=(2.6*Math.pow(1-u,0.85)+0.5)*(d<HEAD?Math.sqrt(Math.max(0,1-((HEAD-d)/HEAD)**2)):1);
  const v0=Math.sin(d*0.7-ph*TAU*3)*0.5;
  for(let q0=-w*1.3;q0<=w*1.3;q0+=0.5){
   const q=Math.abs(q0)/w,y=AY+q0+v0*u;
   const lv=q<0.2?7:q<0.42?6:q<0.66?5:q<0.9?4:3;
   p.px(x,y,PAL[lv]);
  }
 }
 for(const s of [0,Math.PI]){
  for(let d=1.5;d<L*0.72;d+=1){
   const a=d*0.42-ph*TAU*2.6+s,y=AY+Math.sin(a)*(1.9*(1-d/L)+0.5);
   if(Math.cos(a)>0.25)p.dot(AX-d,y,Math.cos(a)>0.75?PAL[7]:PAL[6]);
  }
 }
 p.circle(AX,AY,2.6,PAL[6]);p.circle(AX-1,AY,1.5,PAL[7]);
 p.glow(AX,AY,15,PAL[5],0.5);p.glow(AX-L*0.5,AY,10,PAL[4],0.22);
}
// ---------- 通用命中爆：白热核+放射刺+外扩环+溅射 ----------
function hitBurst(p,AX,AY,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12), k=1-ph;
 const R0=R*0.42*grow;
 for(let i=0;i<8;i++){
  const a=i*TAU/8+ph*2.4,l=R0*(1.5+0.7*Math.sin(ph*TAU*5+i*1.7));
  p.line(AX,AY,AX+Math.cos(a)*l,AY+Math.sin(a)*l,(u)=>(u<0.45?PAL[7]:i%2?PAL[6]:PAL[5]),(u)=>(u<0.5?1:1.5-u));
 }
 p.circle(AX,AY,R0*1.3,PAL[4],k);p.circle(AX,AY,R0,PAL[6],k);p.circle(AX,AY,R0*0.55,PAL[7],k);
 for(let i=0;i<3;i++){
  const q=(((ph*1.8+i/3)%1)+1)%1;
  p.ring(AX,AY,3+R*0.5*ease(q),Math.max(1,2.2*(1-q)),q<0.3?PAL[7]:PAL[5],(1.1-q)*k);
 }
 p.glow(AX,AY,R*0.8,PAL[5],0.7*k);p.glow(AX,AY,R*0.3,PAL[7],0.5*k);
 for(let j=0;j<10;j++){
  const a=hash(j*3+1)*TAU,sp=30+hash(j*7+2)*60,d0=ph*sp;
  const x=AX+Math.cos(a)*d0,y=AY+Math.sin(a)*d0-d0*d0*0.05;
  const kk=1-ph;
  if(kk>0.15)p.disc(x,y,0.8+hash(j)*1.2,j%3?PAL[6]:PAL[7],kk*0.85);
 }
}

// ---------- 通用拖尾: 由头向尾渐细渐暗的波动虚线 ----------
function trailBody(p,ph,PAL){
 for(let d=0;d<120;d+=1){
  const u=d/120,x=-d,y=Math.sin(d*0.22-ph*TAU*2.2)*3.2*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*8))%3)<2)p.px(x,y,PAL[lv]);
  if(d%9===0)p.glow(x,y,3,PAL[5],0.12*(1-u));
 }
 p.glow(0,0,12,PAL[6],0.35);
}

// ---------- 段规格 ----------
const SPECS={
 // 母亲光线(治疗蓝白): start 4帧 96x96 | body 4帧 192x224 behind | beam 4帧 560x64 | hit 4帧 128x128
 'mother_fx_heal_start':{n:4,W:96,H:96,AX:48,AY:48,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   p.circle(0,0,13*k+4,HEAL[4],0.8*k);p.circle(0,0,9*k+2,HEAL[6],k);p.circle(0,0,4.5*k,HEAL[7],k);
   p.glow(0,0,34*k+10,HEAL[5],0.55*k);
   for(let j=0;j<6;j++){const a=hash(j*5+1)*TAU+ph*2.2,d=(1-ph)*20+6,x=Math.cos(a)*d,y=Math.sin(a)*d*0.7;
    p.disc(x,y,1.4,HEAL[6],k*0.8);p.glow(x,y,4,HEAL[5],0.2*k);}
 }},
 'mother_fx_heal_body':{n:4,W:192,H:224,AX:96,AY:112,behind:true,loop:true,draw:(p,ph,t,W,H,AX,AY)=>{
   // 双侧柔光裹身: 竖向流光沿身体两侧上升
   for(let side=-1;side<=1;side+=2){
    for(let u=0;u<1;u+=0.02){
     const ph2=((ph+u*0.9)%1),y=96-u*180,x=side*(30+Math.sin(u*9+ph*6)*6)*Math.sin(ph2*Math.PI);
     if(y<-84||y>8)continue;
     const k=Math.sin(ph2*Math.PI)*0.8;
     p.disc(x,y,1.6,HEAL[5],k);p.disc(x,y,0.8,HEAL[7],k*0.9);
    }
   }
   p.glow(0,-30,40,HEAL[4],0.14);p.glow(0,40,44,HEAL[4],0.12);
 }},
 'mother_fx_heal_beam':{n:4,W:560,H:96,AX:36,AY:48,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,W,H,0,0,516,30,HEAL,ph)},
 'mother_fx_heal_hit':{n:4,W:128,H:128,AX:64,AY:64,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,0,0,46,HEAL,ph,0.36)},
 // 母亲破坏光线(红金): start 4帧 88x88 | body 4帧 192x224 behind | beam 4帧 560x160 | hit 4帧 144x144
 'mother_fx_destruct_start':{n:4,W:88,H:88,AX:44,AY:44,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   for(let i=0;i<5;i++){const a=i*TAU/5-ph*3,l=10*k+4;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?DEST[7]:DEST[5]),(u)=>(u<0.6?1:1.4-u));}
   p.circle(0,0,12*k+4,DEST[4],0.85*k);p.circle(0,0,8*k+2,DEST[6],k);p.circle(0,0,4*k,DEST[7],k);
   p.glow(0,0,32*k+10,DEST[5],0.6*k);
 }},
 'mother_fx_destruct_body':{n:4,W:192,H:224,AX:96,AY:112,behind:true,loop:true,draw:(p,ph,t,W,H,AX,AY)=>{
   for(let side=-1;side<=1;side+=2){
    for(let u=0;u<1;u+=0.02){
     const ph2=((ph+u*0.9)%1),y=96-u*180,x=side*(32+Math.sin(u*9+ph*6)*7)*Math.sin(ph2*Math.PI);
     if(y<-84||y>8)continue;
     const k=Math.sin(ph2*Math.PI)*0.85;
     p.disc(x,y,1.8,DEST[5],k);p.disc(x,y,0.9,DEST[7],k*0.9);
    }
   }
   p.glow(0,-34,42,DEST[4],0.16);p.glow(0,40,46,DEST[4],0.14);
 }},
 'mother_fx_destruct_beam':{n:4,W:560,H:160,AX:40,AY:80,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,W,H,0,0,516,52,DEST,ph)},
 'mother_fx_destruct_hit':{n:4,W:144,H:144,AX:72,AY:72,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,0,0,60,DEST,ph,0.36)},
 // 方向技能光弹(蓝白): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 4帧 112x112
 'mother_fx_ray_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.4+0.6*ph;
   p.circle(0,0,10*k+3,HEAL[5],0.8*k);p.circle(0,0,6*k+1.5,HEAL[7],k);
   p.glow(0,0,24*k+8,HEAL[5],0.55*k);
 }},
 'mother_fx_ray_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,0,0,42,HEAL,ph)},
 'mother_fx_ray_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,HEAL)},
 'mother_fx_ray_hit':{n:4,W:112,H:112,AX:56,AY:56,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,0,0,38,HEAL,ph,0.36)},
 // 母亲淋浴(光雨): start 4帧 192x192 天顶光阵 | drop 6帧 96x192 光柱下降 | burst 4帧 160x128 落地光散
 'mother_fx_rain_start':{n:4,W:192,H:192,AX:96,AY:96,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.4+0.6*ph;
   for(let i=0;i<3;i++){
    const q=(((ph*0.8+i/3)%1)+1)%1;
    p.ring(0,-20,8+52*ease(q),Math.max(1,2.4*(1-q)),q<0.3?RAIN[7]:RAIN[5],(1.1-q)*0.8);
   }
   p.glow(0,-20,40*k+10,RAIN[5],0.4*k);
   for(let j=0;j<8;j++){const a=hash(j*3+1)*TAU,d=16+hash(j*5+2)*50,x=AX+Math.cos(a)*d*1.2,y=AY-20+Math.sin(a)*d*0.7;
    p.disc(x,y,1.6,RAIN[6],0.75*k);p.glow(x,y,4,RAIN[5],0.18*k);}
 }},
 'mother_fx_rain_drop':{n:6,W:96,H:192,AX:48,AY:24,loop:false,draw:(p,ph,t,W,H,AX,AY)=>{
   // 光柱自顶落下: 头部亮团+柱身渐细+散落光点
   const prog=ph; const headY=prog*140;
   for(let d=0;d<90;d+=1){
    const y=headY-d*1.6;if(y<-4||y>150)continue;
    const u=d/90,w=5*(1-u*0.75)+1;
    for(let q0=-Math.round(w);q0<=Math.round(w);q0+=1){
     const q=Math.abs(q0)/w;
     p.px(AX+q0,y,RAIN[q<0.3?7:q<0.6?6:5]);
    }
   }
   p.circle(AX,headY,4,RAIN[7]);p.circle(AX,headY,2.2,RAIN[7]);
   p.glow(AX,headY,18,RAIN[6],0.5);
   for(let j=0;j<5;j++){const x=AX+(hash(j*7+3)-0.5)*22,y=headY-hash(j*5+4)*30-ph*20;
    p.disc(x,y,1+hash(j)*1.2,RAIN[6],0.7);}
 }},
 'mother_fx_rain_burst':{n:4,W:160,H:128,AX:80,AY:96,draw:(p,ph,t,W,H,AX,AY)=>{
   // 落地光散: 沿地面向两侧扩散的光弧+溅起光点
   const k=1-ph;
   for(let s=-1;s<=1;s+=2){
    for(let d=0;d<54;d+=0.8){
     const u=d/54,x=s*d,y=-6-u*16*(1-u)-Math.sin(u*7+ph*8)*2;
     const lv=Math.max(4,Math.floor((1-u)*7));
     if((d*2%3)<2)p.px(x,y,RAIN[Math.min(7,lv+1)]);
    }
   }
   p.glow(0,-4,26*k+8,RAIN[5],0.4*k);
   for(let j=0;j<8;j++){const x=AX+(hash(j*3+1)-0.5)*60,y=AY-4-hash(j*5+2)*26*ph;
    p.disc(x,y,1+hash(j)*1.4,RAIN[6],k*0.8);}
 }},
 // 掌部充能(红金): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 3帧 96x96
 'mother_fx_palm_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   for(let i=0;i<4;i++){const a=i*TAU/4+ph*2.6,l=8*k+3;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?DEST[7]:DEST[5]));}
   p.circle(0,0,9*k+3,DEST[5],0.85*k);p.circle(0,0,5*k+1.5,DEST[7],k);
   p.glow(0,0,22*k+8,DEST[5],0.55*k);
 }},
 'mother_fx_palm_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,0,0,42,DEST,ph)},
 'mother_fx_palm_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,DEST)},
 'mother_fx_palm_hit':{n:3,W:96,H:96,AX:48,AY:48,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,0,0,34,DEST,ph,0.30)},
};
// ---------- 烘焙循环 ----------
const exports=[],bindings={};
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];
 const dur=spec.loop?1.0:spec.n/60;
 for(let i=0;i<spec.n;i++){
  const t=spec.loop?i/60*(1.0/spec.n*spec.n)* (1.0):i/60; // loop: 均匀采样一周期; 非loop: 顺序帧
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
 bindings[id]={id,texture:`res://assets/effects/mother-of-ultra/fx-family-pixelfx-20261111-v1/${id}/atlas.png`,rects,
  anchor:[spec.AX,spec.AY],ticks:4,display_scale:[1,1],behind_fighter:!!spec.behind,full_frame:true,
  source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',
  authoring_source:'res://tools/rebuild/mother-of-ultra/fx-family-pixelfx-20261111-v1/bake.mjs'};
 if(spec.loop)bindings[id].loop=true;
 exports.push({id,n:spec.n,W:spec.W,H:spec.H,anchor:[spec.AX,spec.AY],behind:!!spec.behind,loop:!!spec.loop,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.mother-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:Object.keys(bindings).length}));
