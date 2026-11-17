// PixelFX离线烘焙：盖亚专属特效家族（光子冰刀/量子流线/光子粉碎机/盖亚切割/掌部充能）。
// 全部段真透明像素整帧；不借他人家族，不改人物与判定。照 fx-family（奥母）管线模式。
// 色板：盖亚系红色主调（Photon Edge/Quantum Stream/Photon Crusher/Gaia Slash 均红，取自招式表）。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711112;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function ease(v){return v*v*(3-2*v);}
const NOISE=noiseFor(.4);
const TAU=Math.PI*2;
// 色板（暗→亮）：盖亚红系（暗红→猩红→橙红→白热）
const RED=fit(['#3d0d14','#7a1a24','#b82838','#e84a48','#f87868','#fca88c','#fed4b4','#ffffff'],8);
// 量子流线微偏蓝红（交叉臂超高热，次级资料取红，稍偏洋红以区分冰刀）
const QNT=fit(['#3d0d20','#7a1a3a','#b82858','#e84a7a','#f8789a','#fca8bc','#fed4dc','#ffffff'],8);

// ---------- 通用束体绘制：白热芯带横向脉动、缠绕光丝、端部辉光（照奥母家族） ----------
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
 // 发射端: 旋转光芒+白热圆芯
 const fr=4.5+Math.sin(ph*TAU*9)*0.7;
 for(let i=0;i<4;i++){
  const a=ph*TAU*2.2+i*Math.PI/2,l=7+3*Math.sin(ph*TAU*6+i);
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?PAL[7]:PAL[6]));
 }
 p.circle(0,0,fr+1.4,PAL[5]);p.circle(0,0,fr,PAL[6]);p.circle(0,0,fr*0.55,PAL[7]);
 p.glow(0,0,30,PAL[6],0.75);
 // 端部: 热斑+外扩环
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
// ---------- 通用拖尾：由头向尾渐细渐暗的波动虚线 ----------
function trailBody(p,ph,PAL){
 for(let d=0;d<120;d+=1){
  const u=d/120,x=-d,y=Math.sin(d*0.22-ph*TAU*2.2)*3.2*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*8))%3)<2)p.px(x,y,PAL[lv]);
  if(d%9===0)p.glow(x,y,3,PAL[5],0.12*(1-u));
 }
 p.glow(0,0,12,PAL[6],0.35);
}
// ---------- 盖亚切割三日月镖：新月形红刃，内弧挖空、外弧白热尖 ----------
function crescent(p,R,PAL,ph){
 const spin=ph*TAU*3;
 // 新月: 两圆之间月牙带。外圆 R, 内圆偏移产生月牙
 for(let a=0;a<TAU;a+=0.02){
  const cx=Math.cos(a)*R,cy=Math.sin(a)*R*0.86;
  // 内边界: 圆心偏 (-R*0.38,0) 半径 R*0.86
  const ix=cx+R*0.38,iy=cy;
  const ir2=Math.hypot(ix,iy);
  if(ir2<R*0.86)continue;
  // 相位旋绕: 沿月牙带流光
  const band=((a-spin)/(TAU*0.45))%1;
  const head=band>0?band:band+1;              // 0..1 沿带
  const lv=Math.floor(7-head*head*5.5);       // 头亮尾暗
  const alpha=Math.min(1,(1.1-head)*1.2);
  if(lv<3)continue;
  const wob=1+0.06*Math.sin(a*5+ph*TAU*4);
  p.disc(cx*wob,cy*wob,1.3,PAL[Math.max(3,lv)],alpha);
  if(lv>=6)p.disc(cx*wob,cy*wob,0.6,PAL[7],alpha*0.9);
 }
 // 头部白热尖（旋绕最亮点）与核心辉光
 const ha=spin%(TAU);
 p.disc(Math.cos(ha)*R*0.92,Math.sin(ha)*R*0.92*0.86,2.2,PAL[7],0.95);
 p.glow(Math.cos(ha)*R*0.92,Math.sin(ha)*R*0.92*0.86,12,PAL[6],0.4);
 p.glow(0,0,R*0.9,PAL[5],0.3);
 p.disc(0,0,2.4,PAL[6],0.8);
}
// ---------- 光子冰刀贴头延伸刃：从锚点向前上的弯刃，白热芯红光边 ----------
function edgeBlade(p,ph,PAL){
 // 刃主干: 从 (0,0) 向前延伸 120px, 带轻微上弯
 const L=120;
 for(let d=0;d<=L;d+=0.5){
  const u=d/L;
  const x=d,y=-u*u*16;                        // 上弯
  const w=5.5*(1-u*0.82)+0.8;                 // 根粗尖细
  const shim=Math.sin(d*0.5-ph*TAU*6)*0.7;    // 刃身微颤
  for(let q0=-w;q0<=w;q0+=0.5){
   const q=Math.abs(q0)/w;
   const lv=q<0.2?7:q<0.45?6:q<0.7?5:q<1?4:3;
   p.px(x,y+q0+shim*u,PAL[lv]);
  }
 }
 // 刃脊流光: 沿刃的亮白游丝
 for(let j=0;j<3;j++){
  const off=((ph*1.4+j*0.33)%1);
  const d=off*L,x=d,y=-(d/L)*(d/L)*16;
  p.disc(x,y,1.6,PAL[7],0.9);p.glow(x,y,7,PAL[6],0.3);
 }
 // 刃根: 头部聚能白热核
 p.circle(0,0,7,RED[5],0.9);p.circle(0,0,4.5,RED[6],0.95);p.circle(0,0,2.4,RED[7],1);
 p.glow(0,0,26,RED[5],0.6);
 // 尖端小热斑
 p.glow(L,-16,10,RED[6],0.4);
}

// ---------- 段规格 ----------
const SPECS={
 // 光子冰刀(红刃): start 4帧 72x72 头部聚能 | blade 4帧 176x96 贴头延伸刃 | hit 4帧 128x128
 'gaia_fx_edge_start':{n:4,W:72,H:72,AX:36,AY:36,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   // 头部聚能: 向上的三道短刃脊+白热核
   for(let i=0;i<3;i++){
    const a=-Math.PI/2+(i-1)*0.5,l=14*k+5;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.45?RED[7]:RED[5]),(u)=>(u<0.55?1.1:1.6-u));
   }
   p.circle(0,0,11*k+3,RED[4],0.85*k);p.circle(0,0,7.5*k+2,RED[6],k);p.circle(0,0,3.6*k,RED[7],k);
   p.glow(0,0,30*k+8,RED[5],0.6*k);
   for(let j=0;j<6;j++){const a=hash(j*5+1)*TAU+ph*2.4,d=(1-ph)*18+5;
    p.disc(Math.cos(a)*d,Math.sin(a)*d*0.7,1.3,RED[6],k*0.8);}
 }},
 'gaia_fx_edge_blade':{n:4,W:176,H:96,AX:28,AY:60,draw:(p,ph,t,W,H,AX,AY)=>edgeBlade(p,ph,RED)},
 'gaia_fx_edge_hit':{n:4,W:128,H:128,AX:64,AY:64,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,46,RED,ph,0.36)},
 // 量子流线(交叉臂红洋色粗束): start 4帧 88x88 | beam 4帧 560x96 | hit 4帧 144x144
 'gaia_fx_quantum_start':{n:4,W:88,H:88,AX:44,AY:44,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 交叉双臂聚能: 两组斜向交叉光芒
   for(let s=0;s<2;s++){
    const a=(s?0.62:-0.62)+ph*1.2,l=18*k+6;
    p.line(-Math.cos(a)*l,-Math.sin(a)*l,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?QNT[7]:QNT[5]),(u)=>(u<0.6?1:1.5-u));
   }
   p.circle(0,0,13*k+4,QNT[4],0.85*k);p.circle(0,0,9*k+2,QNT[6],k);p.circle(0,0,4.2*k,QNT[7],k);
   p.glow(0,0,34*k+10,QNT[5],0.6*k);
 }},
 'gaia_fx_quantum_beam':{n:4,W:560,H:96,AX:36,AY:48,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,516,40,QNT,ph)},
 'gaia_fx_quantum_hit':{n:4,W:144,H:144,AX:72,AY:72,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,60,QNT,ph,0.36)},
 // 光子粉碎机(头部光线红金): start 4帧 72x72 三段蓄能 | beam 4帧 560x80 | hit 4帧 136x136
 'gaia_fx_crusher_start':{n:4,W:72,H:72,AX:36,AY:36,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.3+0.7*ph;
   // 三段蓄能: 三圈收缩环依次点亮
   for(let i=0;i<3;i++){
    const q=(((ph*0.9+i/3)%1)+1)%1;
    const r=18-10*i;
    p.ring(0,0,Math.max(2,r*(1-q*0.55)),1.4,q<0.3?RED[7]:RED[5],(0.9-q*0.4)*k);
   }
   p.circle(0,0,12*k+3,RED[4],0.85*k);p.circle(0,0,8*k+2,RED[6],k);p.circle(0,0,3.8*k,RED[7],k);
   p.glow(0,0,30*k+8,RED[5],0.6*k);
 }},
 'gaia_fx_crusher_beam':{n:4,W:560,H:80,AX:36,AY:40,loop:true,draw:(p,ph,t,W,H,AX,AY)=>beamBody(p,516,36,RED,ph)},
 'gaia_fx_crusher_hit':{n:4,W:136,H:136,AX:68,AY:68,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,56,RED,ph,0.36)},
 // 盖亚切割(三日月镖): start 3帧 64x64 | flight 4帧 64x64 新月旋绕 | trail 4帧 160x48 | hit 4帧 112x112
 'gaia_fx_slash_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.4+0.6*ph;
   // 右臂聚能: 弧形刃光渐亮
   p.arc(0,0,14*k+4,2.2,-2.4,-0.6,RED[6],k*0.9);
   p.arc(0,0,10*k+3,1.8,-2.2,-0.8,RED[7],k);
   p.circle(0,0,6*k+2,RED[5],0.85*k);
   p.glow(0,0,24*k+8,RED[5],0.55*k);
 }},
 'gaia_fx_slash_flight':{n:4,W:64,H:64,AX:32,AY:32,loop:true,draw:(p,ph,t,W,H,AX,AY)=>crescent(p,24,RED,ph)},
 'gaia_fx_slash_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,RED)},
 'gaia_fx_slash_hit':{n:4,W:112,H:112,AX:56,AY:56,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,38,RED,ph,0.36)},
 // 掌部充能(红白): start 3帧 64x64 | flight 4帧 56x56 | trail 4帧 160x48 | hit 3帧 96x96
 'gaia_fx_palm_start':{n:3,W:64,H:64,AX:32,AY:32,draw:(p,ph,t,W,H,AX,AY)=>{
   const k=0.35+0.65*ph;
   for(let i=0;i<4;i++){const a=i*TAU/4+ph*2.6,l=8*k+3;
    p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.5?RED[7]:RED[5]));}
   p.circle(0,0,9*k+3,RED[5],0.85*k);p.circle(0,0,5*k+1.5,RED[7],k);
   p.glow(0,0,22*k+8,RED[5],0.55*k);
 }},
 'gaia_fx_palm_flight':{n:4,W:56,H:56,AX:46,AY:28,loop:true,draw:(p,ph,t,W,H,AX,AY)=>boltBody(p,42,RED,ph)},
 'gaia_fx_palm_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,draw:(p,ph,t,W,H,AX,AY)=>trailBody(p,ph,RED)},
 'gaia_fx_palm_hit':{n:3,W:96,H:96,AX:48,AY:48,draw:(p,ph,t,W,H,AX,AY)=>hitBurst(p,34,RED,ph,0.30)},
};
// ---------- 烘焙循环 ----------
const exports=[],bindings={};
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];
 const dur=spec.loop?1.0:spec.n/60;
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
 bindings[id]={id,texture:`res://assets/effects/ultraman-gaia/fx-family-pixelfx-20261111-v1/${id}/atlas.png`,rects,
  anchor:[spec.AX,spec.AY],ticks:4,display_scale:[1,1],behind_fighter:!!spec.behind,full_frame:true,
  source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',
  authoring_source:'res://tools/rebuild/ultraman-gaia/fx-family-pixelfx-20261111-v1/bake.mjs'};
 if(spec.loop)bindings[id].loop=true;
 exports.push({id,n:spec.n,W:spec.W,H:spec.H,anchor:[spec.AX,spec.AY],behind:!!spec.behind,loop:!!spec.loop,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.gaia-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:Object.keys(bindings).length}));
