// PixelFX离线烘焙：佐菲专属特效家族（Z光线电流束/超级冻霜/M87主束/光路掌突/掌部充能）。
// 全部段真透明像素整帧；不借他人家族，不改人物与判定。照 fx-family（奥母）管线模式。
// 色板：佐菲蓝白系（Z光线电流蓝白、超级冻霜淡青白、M87 蓝白主束）。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711103;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function ease(v){return v*v*(3-2*v);}
const NOISE=noiseFor(.4);
const TAU=Math.PI*2;
// 色板（暗→亮）
const BLUE=fit(['#0a1e4d','#143a8f','#2a63cf','#4d8fe8','#7ab4f2','#a8d4f9','#d4ecff','#ffffff'],8);   // Z光线/M87 蓝白
const FROST=fit(['#0e3d4d','#1e6a8a','#3a96c4','#5ab8e0','#88d4ee','#b4e8f7','#dcf6ff','#ffffff'],8);  // 冻霜淡青白

// ---------- 通用束体：白热芯+缠绕光丝+端部辉光（照奥母家族） ----------
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
// ---------- 电流束：Z光线专用。主干锯齿抖动+分叉支流+电火花颗粒 ----------
function boltBeamBody(p,len,thick,PAL,ph){
 // 主干: 逐段带锯齿竖向抖动的粗芯
 for(let d=0;d<=len;d+=0.5){
  const x=d;
  const w=thick*0.5*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/14+0.3);
  const jag=Math.sin(d*0.34+Math.sin(d*0.11+ph*TAU*3)*2.4)*w*0.42;   // 锯齿中线
  for(let q0=-w*1.25;q0<=w*1.25;q0+=0.5){
   const q=Math.abs(q0)/w,y=jag+q0;
   const lv=q<0.2?7:q<0.45?6:q<0.72?5:q<1?4:3;
   p.px(x,y,PAL[lv]);
  }
 }
 // 分叉支流: 4-5 根从主干斜出的细电枝，相位游走
 for(let b=0;b<5;b++){
  const d0=(0.18+hash(b*11+3)*0.64)*len;
  const l=10+hash(b*7+1)*22,dir=(hash(b*5+2)<0.5?-1:1)*(0.35+hash(b*3+4)*0.5);
  const jx=Math.sin(ph*TAU*2.7+b*2.1)*3;
  p.polyline([[d0,0],[d0+l*0.34,dir*l*0.34+jx],[d0+l*0.62,dir*l*0.75-jx],[d0+l,dir*l]],1.1,(u)=>(u<0.4?PAL[7]:u<0.75?PAL[6]:PAL[5]));
 }
 // 电火花颗粒: 沿干散布的短亮线
 for(let j=0;j<14;j++){
  const d0=hash(j*13+5)*len,y0=(hash(j*7+6)-0.5)*thick*1.1;
  const l=2+hash(j*3+7)*4,a=hash(j*11+8)*TAU+ph*TAU*4;
  p.line(d0,y0,d0+Math.cos(a)*l,y0+Math.sin(a)*l,PAL[j%2?7:6]);
 }
 // 发射端: 白热圆芯+旋转光芒
 const fr=4.2+Math.sin(ph*TAU*9)*0.6;
 for(let i=0;i<4;i++){
  const a=ph*TAU*2.2+i*Math.PI/2,l=7+2.6*Math.sin(ph*TAU*6+i);
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?PAL[7]:PAL[6]));
 }
 p.circle(0,0,fr+1.3,PAL[5]);p.circle(0,0,fr,PAL[6]);p.circle(0,0,fr*0.5,PAL[7]);
 p.glow(0,0,30,PAL[6],0.75);
 // 端部: 热斑+外扩环
 const ir=4.2+Math.sin(ph*TAU*11)*0.6;
 for(let k=0;k<2;k++){
  const q=(((ph*2.6+k/2)%1)+1)%1;
  p.ring(len,0,3+10*ease(q),Math.max(1,2*(1-q)),q<0.3?PAL[7]:PAL[5],1.05-q);
 }
 p.circle(len,0,ir+1.1,PAL[4]);p.circle(len,0,ir,PAL[6]);p.circle(len,0,ir*0.5,PAL[7]);
 p.glow(len,0,32,PAL[5],0.8);
}
// ---------- 冷冻锥：前尖后宽锥体+内部冰晶+外缘霜雾 ----------
function frostCone(p,L,PAL,ph){
 // 锥体: 锥尖在锚点(0,0)朝前, 锥尾向左(-L)渐宽
 const W=14;
 for(let d=0;d<=L;d+=0.5){
  const x=-d;                                  // 向左延伸
  const u=d/L;
  const w=W*u*0.9+0.8;                         // 尖细尾粗
  const wob=Math.sin(d*0.3-ph*TAU*2.4)*0.5;
  for(let q0=-w*1.3;q0<=w*1.3;q0+=0.5){
   const q=Math.abs(q0)/w;
   const lv=q<0.18?7:q<0.4?6:q<0.65?5:q<0.9?4:3;
   p.px(x,wob+q0,PAL[lv]);
  }
 }
 // 内部冰晶: 菱形小晶体沿锥分布, 微闪
 for(let j=0;j<7;j++){
  const d0=(0.15+hash(j*9+1)*0.7)*L;
  const r=1.2+hash(j*5+2)*2.2;
  const tw=(0.6+0.4*Math.sin(ph*TAU*3+j*1.3));
  const y0=(hash(j*3+3)-0.5)*10;
  const cx=-d0;
  // 菱形四点
  p.line(cx-r,y0,cx,y0-r,PAL[6],tw);p.line(cx,y0-r,cx+r,y0,PAL[6],tw);
  p.line(cx+r,y0,cx,y0+r,PAL[6],tw);p.line(cx,y0+r,cx-r,y0,PAL[6],tw);
  p.disc(cx,y0,0.7,PAL[7],tw);
 }
 // 霜雾颗粒: 尾部外缘飘散的冷光点
 for(let j=0;j<9;j++){
  const d0=hash(j*7+4)*L*0.6,s=1.4+hash(j*3+5)*2;
  const a=TAU*hash(j*11+6)+ph*TAU*1.8;
  const x=-d0+Math.cos(a)*s,y=Math.sin(a)*s*0.5;
  const k=(0.5+0.5*Math.sin(ph*TAU*2.6+j*2.2));
  p.disc(x,y,0.9+hash(j)*0.9,PAL[5],k*0.7);
 }
 // 锥尖冷光核(锚点处)
 p.circle(0,0,3.4,PAL[6]);p.circle(0,0,2,PAL[7]);
 p.glow(0,0,16,PAL[5],0.6);p.glow(-L*0.5,0,10,PAL[4],0.25);
}
// ---------- 通用飞行弹：白热圆头+带状尾锥+缠绕火星（照奥母家族） ----------
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
// ---------- 通用命中爆：白热核+放射刺+外扩环+溅射（照奥母家族） ----------
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
// ---------- 电流命中爆：放射刺改锯齿电枝 ----------
function electricHit(p,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12), k=1-ph;
 const R0=R*0.42*grow;
 for(let i=0;i<7;i++){
  // 锯齿电枝: 中途折一次的放电
  const a=i*TAU/7+ph*2.4,l=R0*(1.5+0.6*Math.sin(ph*TAU*5+i*1.7));
  const bend=0.4*Math.sin(i*2.1+ph*9);
  p.polyline([[0,0],[Math.cos(a)*l*0.5,Math.sin(a)*l*0.5],[Math.cos(a+bend)*l,Math.sin(a+bend)*l]],1.3,(u)=>(u<0.4?PAL[7]:i%2?PAL[6]:PAL[5]));
 }
 p.circle(0,0,R0*1.3,PAL[4],k);p.circle(0,0,R0,PAL[6],k);p.circle(0,0,R0*0.55,PAL[7],k);
 for(let i=0;i<3;i++){
  const q=(((ph*1.8+i/3)%1)+1)%1;
  p.ring(0,0,3+R*0.5*ease(q),Math.max(1,2.2*(1-q)),q<0.3?PAL[7]:PAL[5],(1.1-q)*k);
 }
 p.glow(0,0,R*0.8,PAL[5],0.7*k);p.glow(0,0,R*0.3,PAL[7],0.5*k);
 for(let j=0;j<9;j++){
  const a=hash(j*3+1)*TAU,sp=28+hash(j*7+2)*55,d0=ph*sp;
  const x=Math.cos(a)*d0,y=Math.sin(a)*d0-d0*d0*0.05;
  if(1-ph>0.15)p.disc(x,y,0.8+hash(j)*1.1,j%3?PAL[6]:PAL[7],(1-ph)*0.85);
 }
}
// ---------- 冻霜命中爆：冰晶六芒+外扩环+落霜颗粒 ----------
function frostHit(p,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12), k=1-ph;
 const R0=R*0.42*grow;
 // 六芒冰晶刺
 for(let i=0;i<6;i++){
  const a=i*TAU/6+ph*0.8,l=R0*(1.5+0.5*Math.sin(ph*TAU*4+i*2.1));
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.45?PAL[7]:PAL[5]),(u)=>(u<0.5?1:1.4-u));
 }
 p.circle(0,0,R0*1.3,PAL[4],k);p.circle(0,0,R0,PAL[6],k);p.circle(0,0,R0*0.55,PAL[7],k);
 for(let i=0;i<3;i++){
  const q=(((ph*1.8+i/3)%1)+1)%1;
  p.ring(0,0,3+R*0.5*ease(q),Math.max(1,2.2*(1-q)),q<0.3?PAL[7]:PAL[5],(1.1-q)*k);
 }
 p.glow(0,0,R*0.8,PAL[5],0.7*k);p.glow(0,0,R*0.3,PAL[7],0.5*k);
 // 落霜: 缓慢下坠的冰点
 for(let j=0;j<10;j++){
  const x=(hash(j*3+1)-0.5)*R*1.6,y=-R*0.4+ph*(30+hash(j*5+2)*40);
  const kk=1-ph;
  if(kk>0.15)p.disc(x,y,0.8+hash(j)*1.1,j%3?PAL[6]:PAL[7],kk*0.8);
 }
}
// ---------- 通用拖尾 ----------
function trailBody(p,ph,PAL){
 for(let d=0;d<120;d+=1){
  const u=d/120,x=-d,y=Math.sin(d*0.22-ph*TAU*2.2)*3.2*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*8))%3)<2)p.px(x,y,PAL[lv]);
  if(d%9===0)p.glow(x,y,3,PAL[5],0.12*(1-u));
 }
 p.glow(0,0,12,PAL[6],0.35);
}
// ---------- 冻霜拖尾：飘散冰尘 ----------
function frostTrail(p,ph,PAL){
 for(let d=0;d<120;d+=1){
  const u=d/120,x=-d;
  const wob=Math.sin(d*0.3-ph*TAU*2.4)*2.2*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*7))%3)<2)p.px(x,wob,PAL[lv]);
  if(d%7===0){const k=(1-u)*(0.4+0.3*Math.sin(ph*TAU*3+d));p.disc(x,wob,1,PAL[6],Math.max(0,k));}
 }
 p.glow(0,0,12,PAL[6],0.35);
}

// ---------- 段规格 ----------
const SPECS={
 // Z光线(蓝白电流短束): start 4帧 80x80 双掌合拢蓄能 | beam 4帧 400x96 锯齿电流束 | hit 4帧 120x120 电流爆
 'zoffy_fx_zray_start':{n:4,W:80,H:80,AX:40,AY:40,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   // 双掌合拢: 两股对向电流弧向中心汇聚
   for(let s=-1;s<=1;s+=2){
    for(let u=0;u<1;u+=0.04){
     const x=s*(26-u*22*k),y=Math.sin(u*7-ph*TAU*4)*2.4;
     const lv=Math.min(7,3+Math.floor(u*4*k));
     p.disc(x,y,1.2+k,BLUE[lv],(0.5+0.5*k)*Math.min(1,u*2+0.3));
    }
   }
   p.circle(0,0,11*k+3,BLUE[4],0.85*k);p.circle(0,0,7*k+2,BLUE[6],k);p.circle(0,0,3.4*k,BLUE[7],k);
   p.glow(0,0,28*k+8,BLUE[5],0.6*k);
   // 短电枝
   for(let j=0;j<5;j++){const a=hash(j*3+1)*TAU+ph*3,l=6*k+3;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,BLUE[j%2?7:6]);}
 }},
 'zoffy_fx_zray_beam':{n:4,W:400,H:96,AX:36,AY:48,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBeamBody(p,324,26,BLUE,ph)},
 'zoffy_fx_zray_hit':{n:4,W:120,H:120,AX:60,AY:60,draw:(p,ph,t,W,H,AX,AY)=>electricHit(p,42,BLUE,ph,0.36)},
 // 超级冻霜(淡青白锥弹): start 4帧 72x72 | flight 4帧 112x64 冷冻锥 | trail 4帧 160x48 冰尘 | hit 4帧 128x128 六芒冰晶
 'zoffy_fx_frost_start':{n:4,W:72,H:72,AX:36,AY:36,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   // 双掌前推: 锥形渐成
   for(let i=0;i<3;i++){
    const q=(((ph*0.9+i/3)%1)+1)%1;
    p.ring(0,0,4+14*k*ease(1-q),1.3,q<0.3?FROST[7]:FROST[5],(1-q)*k*0.9);
   }
   p.circle(0,0,10*k+3,FROST[4],0.85*k);p.circle(0,0,6.5*k+2,FROST[6],k);p.circle(0,0,3.2*k,FROST[7],k);
   p.glow(0,0,26*k+8,FROST[5],0.6*k);
   // 冰尘浮点
   for(let j=0;j<6;j++){const a=hash(j*7+2)*TAU,d=(1-ph)*16+4;
    p.disc(Math.cos(a)*d,Math.sin(a)*d*0.7,1.1,FROST[6],k*0.75);}
 }},
 'zoffy_fx_frost_flight':{n:4,W:112,H:64,AX:92,AY:32,loop:true,draw:(p,ph,t,W,H,AX,AY)=>frostCone(p,86,FROST,ph)},
 'zoffy_fx_frost_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>frostTrail(p,ph,FROST)},
 'zoffy_fx_frost_hit':{n:4,W:128,H:128,AX:64,AY:64,draw:(p,ph,t,W,H,AX,AY)=>frostHit(p,44,FROST,ph,0.36)},
 // M87光线A型(蓝白主束): start 4帧 88x88 | beam 4帧 600x104 最粗主束 | hit 4帧 144x144
 'zoffy_fx_m87_start':{n:4,W:88,H:88,AX:44,AY:44,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 右指尖聚能: 多圈收缩环+白热核
   for(let i=0;i<3;i++){
    const q=(((ph*0.85+i/3)%1)+1)%1;
    p.ring(0,0,16-9*i,1.5,q<0.3?BLUE[7]:BLUE[5],(0.95-q*0.45)*k);
   }
   p.circle(0,0,12*k+4,BLUE[4],0.85*k);p.circle(0,0,8.5*k+2,BLUE[6],k);p.circle(0,0,4*k,BLUE[7],k);
   p.glow(0,0,32*k+10,BLUE[5],0.6*k);
 }},
 'zoffy_fx_m87_beam':{n:4,W:600,H:104,AX:36,AY:52,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,556,44,BLUE,ph)},
 'zoffy_fx_m87_hit':{n:4,W:144,H:144,AX:72,AY:72,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,58,BLUE,ph,0.36)},
 // 光路掌突(蓝白): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 4帧 112x112 电流爆
 'zoffy_fx_raid_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.4+0.6*ph;
   p.circle(0,0,9*k+3,BLUE[5],0.85*k);p.circle(0,0,5.5*k+1.5,BLUE[7],k);
   p.glow(0,0,24*k+8,BLUE[5],0.55*k);
   for(let j=0;j<3;j++){const a=hash(j*5+3)*TAU+ph*2.8,l=7*k+2;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,BLUE[j%2?7:6]);}
 }},
 'zoffy_fx_raid_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,42,BLUE,ph)},
 'zoffy_fx_raid_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,BLUE)},
 'zoffy_fx_raid_hit':{n:4,W:112,H:112,AX:56,AY:56,draw:(p,ph,t,W,H,AX,AY)=>electricHit(p,36,BLUE,ph,0.33)},
 // 掌部充能·崩掌(蓝白): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 4帧 104x104 电流爆
 'zoffy_fx_charge_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   for(let i=0;i<4;i++){const a=i*TAU/4+ph*2.6,l=8*k+3;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?BLUE[7]:BLUE[5]));}
   p.circle(0,0,9*k+3,BLUE[5],0.85*k);p.circle(0,0,5*k+1.5,BLUE[7],k);
   p.glow(0,0,22*k+8,BLUE[5],0.55*k);
 }},
 'zoffy_fx_charge_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,42,BLUE,ph)},
 'zoffy_fx_charge_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,BLUE)},
 'zoffy_fx_charge_hit':{n:4,W:104,H:104,AX:52,AY:52,draw:(p,ph,t,W,H,AX,AY)=>electricHit(p,33,BLUE,ph,0.30)},
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
 bindings[id]={id,texture:`res://assets/effects/zoffy/fx-family-pixelfx-20261111-v1/${id}/atlas.png`,rects,
  anchor:[spec.AX,spec.AY],ticks:4,display_scale:[1,1],behind_fighter:!!spec.behind,full_frame:true,
  source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',
  authoring_source:'res://tools/rebuild/zoffy/fx-family-pixelfx-20261111-v1/bake.mjs'};
 if(spec.loop)bindings[id].loop=true;
 exports.push({id,n:spec.n,W:spec.W,H:spec.H,anchor:[spec.AX,spec.AY],behind:!!spec.behind,loop:!!spec.loop,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.zoffy-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:Object.keys(bindings).length}));
