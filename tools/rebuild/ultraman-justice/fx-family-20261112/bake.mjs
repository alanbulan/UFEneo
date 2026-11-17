// PixelFX 离线烘焙：杰斯提斯专属特效家族（掌弹 / 光线 / 光箭 / Q 蓄气）。
// 全部段真透明像素整帧；形状由本文件绘制函数原创，不读他人特效图集。
// 配色按杰斯提斯标准型：银白亮芯、冰蓝内焰、银红/赤红外焰；不使用赛罗青蓝、
// 泰罗火焰或共享 beam_loop/pulse/special_arrow 的轮廓。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=121112;
const SHA=b=>createHash('sha256').update(b).digest('hex');
const TAU=Math.PI*2;

// 银白→冰蓝→粉红→赤红→暗红：亮芯/内焰/外焰三层次，末两级为暗轮廓。
const BOLT=fit(['#04060c','#0a1020','#1a1430','#3c1a30','#6e2034','#a82c42','#d85064','#f0909c','#a8e0f8','#ffffff'],10);
const BEAM=fit(['#04060c','#081020','#121a34','#2e1c38','#561c30','#842438','#b83a50','#e07c8c','#a8e0f8','#ffffff'],10);
const HIT =fit(['#04060c','#0a1020','#1a1430','#3c1a30','#6e2034','#a82c42','#d85064','#f0909c','#c8ecff','#ffffff'],10);
const CHARGE=fit(['#04060c','#0a1020','#1a1430','#3c1a30','#6e2034','#a82c42','#d85064','#f0909c','#b8e8ff','#ffffff'],10);

function h2(x,y,s){let n=(Math.imul(x|0,374761393)+Math.imul(y|0,668265263)+Math.imul(s|0,2246822519))>>>0;n=Math.imul(n^(n>>>13),1274126177);return((n^(n>>>16))>>>0)/4294967295;}
function clamp(v,a,b){return v<a?a:v>b?b:v;}

// 0=最亮芯，1=最外暗轮廓；固定分层让每帧都能读出亮芯/内焰/外焰。
function levelFor(q){
 if(q<0.10)return 9;
 if(q<0.24)return 8;
 if(q<0.42)return 7;
 if(q<0.60)return 6;
 if(q<0.76)return 5;
 if(q<0.88)return 4;
 if(q<0.96)return 2;
 return 1;
}

// ---------- 掌弹飞行：前尖后收的银白弹头，冰蓝内层，尾焰分叉 ----------
function pulseCenter(x,ph){
 if(x<=8){const t=Math.min(1,(8-x)/46);return Math.sin(x*0.23-ph*TAU*2.0)*2.8*t;}
 return Math.sin(ph*TAU*2)*0.8;
}
function pulseHalf(x,ph){
 if(x<=8){const t=Math.min(1,(8-x)/46);return (1.0+10.5*Math.pow(1-t,0.85))*(1+0.10*Math.sin(x*0.85-ph*TAU*4)+0.06*Math.sin(x*2.05+ph*TAU*3));}
 const u=(x-8)/20;if(u>1)return 0;
 return 10.5*Math.sqrt(Math.max(0,1-u*u))*(1+0.08*Math.sin(ph*TAU*3));
}
function drawPulseBolt(p,ph,fi){
 for(let x=-38;x<=28;x++){
  const w=pulseHalf(x,ph);if(w<0.6)continue;
  const cy=pulseCenter(x,ph);
  for(let y=Math.floor(cy-w);y<=Math.ceil(cy+w);y++){
   const q=Math.abs(y-cy)/w;if(q>1)continue;
   let lv=levelFor(q);
   if(q<0.20)lv=9;else if(q<0.36)lv=8;
   if(q<0.9&&h2(x,y,fi*19+5)>0.87)lv=Math.min(9,lv+2);
   p.px(x,y,BOLT[lv]);
  }
 }
 // 尾部 4 簇分叉火舌，根部压在弹体边缘上，保持单连通。
 for(let k=0;k<4;k++){
  const bx=-34+k*8+Math.round(2*Math.sin(ph*TAU*2+k*1.7));
  const dir=k%2?1:-1;
  const len=Math.round(5+4*(0.5+0.5*Math.sin(ph*TAU*2+k*2.1)));
  const base=pulseCenter(bx,ph)+dir*(pulseHalf(bx,ph)-2);
  for(let i=0;i<=len+2;i++){
   const spread=Math.max(0,Math.round((1-i/(len+2))*2.4));
   for(let dx=-spread;dx<=spread;dx++){
    p.px(bx+dx,base+dir*i,BOLT[i<len*0.38?7:(i<len*0.75?5:2)]);
   }
  }
 }
 // 弹头十字星与白核；粗 2px 保证硬 Alpha 下仍连通。
 for(let a=0;a<4;a++){
  const ang=a*Math.PI/2+ph*TAU*0.25;
  const len=6+3*Math.sin(ph*TAU*2+a);
  p.beam(10,0,10+Math.cos(ang)*len,Math.sin(ang)*len,2.2,a%2?BOLT[8]:BOLT[9]);
 }
 p.beam(7,0,16,0,3.2,BOLT[9]);
 p.px(10,1,BOLT[9]);p.px(10,-1,BOLT[9]);
}

// ---------- 光箭飞行：长杆菱形箭镞，后掠双翼，尾焰与银红箭脊 ----------
function drawArrowFlight(p,ph,fi){
 // 箭杆：-38..8，冰蓝芯、赤红外缘。
 for(let x=-38;x<=10;x++){
  const w=2.6+1.2*Math.sin(x*0.5+ph*TAU*2)*(x<-24?1:0.4);
  const cy=Math.sin(x*0.3-ph*TAU*2)*0.8;
  for(let y=Math.floor(cy-w);y<=Math.ceil(cy+w);y++){
   const q=Math.abs(y-cy)/w;if(q>1)continue;
   let lv=q<0.28?9:q<0.55?8:q<0.8?6:4;
   if(((x+Math.floor(ph*8))%13+13)%13===0)lv=9;
   p.px(x,y,BOLT[lv]);
  }
 }
 // 箭镞：x=8..28 的菱形，白热芯 + 冰蓝刃口。
 for(let x=8;x<=28;x++){
  const w=(x<=17?(x-7)*0.95:(28-x)*0.95);
  for(let y=-Math.ceil(w);y<=Math.ceil(w);y++){
   const q=Math.abs(y)/Math.max(0.6,w);if(q>1)continue;
   let lv=q<0.22?9:q<0.48?8:q<0.76?7:5;
   if(q>0.78&&((x+y+Math.floor(ph*6))%5+5)%5<2)lv=6;
   p.px(x,y,BOLT[lv]);
  }
 }
 // 后掠双翼：从杆尾 -18 起向 -34 展开，根部连在箭杆上。
 for(const dir of [-1,1]){
  for(let i=0;i<=16;i++){
   const x=-18-i;
   const h=Math.round(1+8*(i/16));
   for(let y=1;y<=h;y++){
    const lv=y<h*0.45?6:(y<h*0.8?4:2);
    p.px(x,dir*(3+y),BOLT[lv]);
   }
  }
 }
 // 尾焰：三束短火舌，根部贴翼后缘。
 for(let k=0;k<3;k++){
  const bx=-34-k*3+Math.round(2*Math.sin(ph*TAU*2+k));
  const dir=k%2?1:-1;
  const len=4+3*(0.5+0.5*Math.sin(ph*TAU*2+k*2.4));
  for(let i=0;i<=len;i++){
   const spread=Math.max(0,Math.round((1-i/len)*2));
   for(let dx=-spread;dx<=spread;dx++)p.px(bx-dx,dir*(6+i),BOLT[i<len*0.35?7:(i<len*0.7?5:2)]);
  }
 }
 // 箭镞尖的十字闪与白核。
 p.beam(18,0,29,0,2.6,BOLT[9]);
 for(let a=0;a<4;a++){
  const ang=a*Math.PI/2+ph*TAU*0.25;
  const len=5+2.5*Math.sin(ph*TAU*2+a*1.3);
  p.beam(17,0,17+Math.cos(ang)*len,Math.sin(ang)*len,1.7,a%2?BOLT[8]:BOLT[9]);
 }
}

// ---------- 光线束：可平铺横段，白芯/冰蓝内焰/银红外焰，刃口缺口推进 ----------
function drawBeamTile(p,ph,fi,W,H){
 const cy=0;
 for(let x=0;x<W;x++){
  const u=x/W;
  const core=7.2+1.6*Math.sin(TAU*2*u+ph*TAU*2)+1.0*Math.sin(TAU*5*u-ph*TAU*4);
  const outer=20+5.5*Math.sin(TAU*3*u+ph*TAU*2)+2.5*Math.sin(TAU*7*u-ph*TAU*3);
  const notch=((x+Math.floor(ph*W*0.5))%48+48)%48<7;
  for(let y=-Math.ceil(outer);y<=Math.ceil(outer);y++){
   const q=Math.abs(y)/outer;
   const inCore=Math.abs(y)<=core;
   // 仅外焰的周期缺口，白芯始终连续，保证整段单连通。
   if(!inCore&&notch&&q>0.62)continue;
   let lv;
   if(q<0.20)lv=9;
   else if(q<0.38)lv=8;
   else if(q<0.55)lv=7;
   else if(q<0.72)lv=6;
   else if(q<0.86)lv=4;
   else lv=2;
   // 外缘锯齿：按相位前后推进的短刃。
   if(q>0.78){
    const fang=Math.sin(x*0.42-ph*TAU*3+y*0.9);
    if(fang<0.15)continue;
    if(fang>0.78)lv=6;
   }
   if(inCore&&h2(x,y,fi*23+11)>0.88)lv=9;
   p.px(x,y,BEAM[lv]);
  }
  // 亮芯内的推进短划，仍压在连续白芯上。
  if(((x+Math.floor(ph*32))%24+24)%24<5)p.px(x,0,BEAM[9]);
 }
 // 外焰上的周期亮结，根部连着外焰，不是独立颗粒。
 for(let k=0;k<6;k++){
  const x=Math.round((k/6+ph*0.13)*W)%W;
  const yy=Math.round(10+4*Math.sin(ph*TAU*2+k*1.4));
  for(const s of [-1,1]){
   p.disc(x,s*yy,1.6,BEAM[6]);
   p.px(x,s*(yy-1),BEAM[8]);
  }
 }
}

// ---------- 命中爆：白热核 + 长短放射刃 + 刃间蛛网弧；全部在核心处连通 ----------
function drawHitBurst(p,R,ph,fi,dur,PAL){
 const grow=Math.min(1,(ph*dur)/0.10),k=1-ph;
 const base=R*(0.42+0.34*grow)*(0.62+0.38*Math.sin(Math.min(1,ph*1.7)*Math.PI*0.5));
 const N=10;
 for(let y=-R;y<=R;y++){
  for(let x=-R;x<=R;x++){
   const r=Math.hypot(x,y);if(r>R)continue;
   const a=Math.atan2(y,x);
   const ray=Math.pow(0.5+0.5*Math.cos(a*N+ph*TAU*2+0.4),2.6);
   const tip=base*(0.42+0.68*ray)*(1+0.10*Math.sin(a*7-ph*TAU*3));
   if(r>tip)continue;
   const q=r/Math.max(1,tip);
   let lv=q<0.18?9:q<0.34?8:q<0.52?7:q<0.70?6:q<0.84?5:q<0.94?4:2;
   // 放射刃之间的蛛网弧：只在射线间隙出现，端点接上相邻刃。
   if(ray<0.34&&r>base*0.42&&r<base*0.52){
    const dash=((Math.floor(a*14+ph*6))%3+3)%3;
    if(dash===0)lv=5;
    else continue;
   }
   if(h2(x,y,fi*29+7)>0.90)lv=Math.min(9,lv+2);
   p.px(x,y,PAL[lv]);
  }
 }
 // 中心白核与四向短闪。
 p.circle(0,0,Math.max(2.4,base*0.18),PAL[9]);
 for(let a=0;a<4;a++){
  const ang=a*Math.PI/2+ph*TAU*0.25;
  const len=base*(0.55+0.18*Math.sin(ph*TAU*2+a));
  p.beam(0,0,Math.cos(ang)*len,Math.sin(ang)*len,2.4,a%2?PAL[8]:PAL[9]);
 }
}

// ---------- Q 蓄气：开口向下的银红/冰蓝环，外焰刃、环上亮结与底部回流 ----------
const QW=384,QH=256,QAX=192,QAY=246,QCY=-100,QRX=88,QRY=86;
function drawCharge(p,t,env,fi){
 const time=t/60, gap=TAU*0.03, start=Math.PI+gap, span=TAU-2*gap; // 底部留 33px 开口
 const nodes=8;
 const wobAt=(a)=>1+0.060*Math.sin(a*5+time*2.1)+0.035*Math.sin(a*11-time*3.2);
 for(let i=0;i<=720;i++){
  const a=start+span*(i/720); // 从左下口沿左/顶/右绕到右下口
  const wob=wobAt(a),rx=QRX*wob,ry=QRY*wob;
  const x=Math.sin(a)*rx,y=QCY-Math.cos(a)*ry;
  const w=(5.5+3.2*Math.sin(a*6+time*3.0)+2.5*env)*(0.45+0.55*env);
  // 环带：内缘冰蓝(-3..-1)、白芯(0..0.35w)、粉红过渡、赤红外焰、暗红外缘。
  for(let d=-3;d<=Math.ceil(w);d++){
   let lv;
   if(d<-2)lv=2;
   else if(d<0)lv=8;
   else if(d<w*0.35)lv=9;
   else if(d<w*0.60)lv=7;
   else if(d<w*0.85)lv=6;
   else lv=4;
   const xx=x+Math.sin(a)*d,yy=y-Math.cos(a)*d;
   if(h2(Math.round(xx),Math.round(yy),fi*31+13)>0.92)lv=Math.min(9,lv+1);
   p.px(Math.round(xx),Math.round(yy),CHARGE[lv]);
  }
  // 外缘火舌：每 12° 一簇，根部压进环带，赤红为主、尖端暗红。
  if(i%24===0){
   const k=(i/24)%30;
   const len=Math.round((6+8*(0.5+0.5*Math.sin(a*7+time*4+k)))*env);
   for(let d=Math.floor(w)-1;d<w+len;d++){
    const u=Math.max(0,(d-w)/Math.max(1,len));
    const spread=Math.max(0,Math.round((1-u)*2.6));
    for(let dx=-spread;dx<=spread;dx++){
     const xx=x+Math.sin(a)*d+dx*Math.cos(a),yy=y-Math.cos(a)*d+dx*Math.sin(a);
     let lv=u<0.35?6:(u<0.72?5:3);
     if(Math.abs(dx)===0&&u<0.2)lv=7;
     p.px(Math.round(xx),Math.round(yy),CHARGE[lv]);
    }
   }
   // 内缘倒刺，朝向人物，根部同样压进环带。
   if(k%2===0){
    const il=Math.round((4+4*(0.5+0.5*Math.sin(a*9-time*3)))*env);
    for(let d=-3;d>-3-il;d--){
     const u=Math.max(0,(-3-d)/Math.max(1,il));
     const spread=Math.max(0,Math.round((1-u)*2));
     for(let dx=-spread;dx<=spread;dx++){
      const xx=x+Math.sin(a)*d+dx*Math.cos(a),yy=y-Math.cos(a)*d+dx*Math.sin(a);
      p.px(Math.round(xx),Math.round(yy),CHARGE[u<0.45?8:(u<0.8?5:2)]);
     }
    }
   }
  }
 }
 // 环上旋转亮结：白核压在环带白芯上，不是独立颗粒。
 for(let k=0;k<nodes;k++){
  const a=start+span*(((k/nodes+time*0.11)%1));
  const wob=wobAt(a),x=Math.sin(a)*QRX*wob,y=QCY-Math.cos(a)*QRY*wob;
  p.disc(x,y,2.4+0.8*Math.sin(time*5+k),CHARGE[9]);
  p.disc(x,y,4.0,CHARGE[7],0.9);
 }
 // 底部两端回流：从环口端点向脚心收的断弧，端点重合在环上。
 const endX=Math.sin(start)*QRX,endY=QCY-Math.cos(start)*QRY;
 for(const side of [-1,1]){
  p.disc(side*endX,endY,2.4,CHARGE[8]);
  for(let i=0;i<=22;i++){
   const u=i/22;
   const x=side*Math.abs(endX)*(1-0.66*u);
   const y=endY+2.5*Math.sin(u*Math.PI)+1.2*Math.sin(time*4+i*0.5);
   p.px(Math.round(x),Math.round(y),CHARGE[u<0.4?8:(u<0.75?5:2)]);
  }
 }
 // 顶部汇聚光：按顶部实际摆动半径压在环带上。
 const topY=QCY-QRY*wobAt(TAU);
 p.disc(0,topY,3.0+0.8*Math.sin(time*5.2),CHARGE[9]);
 p.disc(0,topY,5.6,CHARGE[7],0.85);
}

// ---------- 段规格 ----------
const SPECS={
 'justice_fx_pulse_flight':{n:4,W:96,H:64,AX:48,AY:32,loop:true,layer:'flight',pal:BOLT,draw:(p,ph,fi)=>drawPulseBolt(p,ph,fi)},
 'justice_fx_pulse_hit':{n:4,W:128,H:128,AX:64,AY:64,loop:false,layer:'impact',pal:HIT,draw:(p,ph,fi)=>drawHitBurst(p,56,ph,fi,0.34,HIT)},
 'justice_fx_beam':{n:4,W:192,H:112,AX:0,AY:56,loop:true,layer:'beam',pal:BEAM,draw:(p,ph,fi,W,H)=>drawBeamTile(p,ph,fi,W,H),xEdges:true},
 'justice_fx_beam_hit':{n:4,W:128,H:128,AX:64,AY:64,loop:false,layer:'impact',pal:HIT,draw:(p,ph,fi)=>drawHitBurst(p,58,ph,fi,0.36,HIT)},
 'justice_fx_arrow_flight':{n:4,W:112,H:64,AX:56,AY:32,loop:true,layer:'flight',pal:BOLT,draw:(p,ph,fi)=>drawArrowFlight(p,ph,fi)},
 'justice_fx_arrow_hit':{n:4,W:128,H:128,AX:64,AY:64,loop:false,layer:'impact',pal:HIT,draw:(p,ph,fi)=>drawHitBurst(p,52,ph,fi,0.38,HIT)},
};

// ---------- 烘焙循环 ----------
function hashRgba(rgba){return SHA(Buffer.from(rgba.buffer,rgba.byteOffset,rgba.byteLength));}
function keepLargest(rgba,W,H){
 const n=W*H,seen=new Uint8Array(n),comp=[];
 const idx=(x,y)=>y*W+x;
 const on=(i)=>rgba[i*4+3]>0;
 for(let i=0;i<n;i++){
  if(!on(i)||seen[i])continue;
  const stack=[i];seen[i]=1;const cells=[];
  while(stack.length){
   const j=stack.pop();cells.push(j);
   const x=j%W,y=(j/W)|0;
   for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=W||ny>=H)continue;
    const k=idx(nx,ny);if(on(k)&&!seen[k]){seen[k]=1;stack.push(k);}
   }
  }
  comp.push(cells);
 }
 comp.sort((a,b)=>b.length-a.length);
 for(let c=1;c<comp.length;c++)for(const i of comp[c])rgba.fill(0,i*4,i*4+4);
 return comp.map(c=>c.length);
}
function quantize(rgba,W,H,pal){
 for(let i=0;i<W*H;i++){
  const a=rgba[i*4+3];
  if(a<128){rgba.fill(0,i*4,i*4+4);continue;}
  rgba[i*4+3]=255;
  let best=0,bestD=1e18;
  for(let k=0;k<pal.length;k++){
   const c=pal[k],r=(c&255),g=((c>>>8)&255),b=((c>>>16)&255);
   const dr=rgba[i*4]-r,dg=rgba[i*4+1]-g,db=rgba[i*4+2]-b,d=dr*dr+dg*dg+db*db;
   if(d<bestD){bestD=d;best=k;}
  }
  const c=pal[best];rgba[i*4]=c&255;rgba[i*4+1]=(c>>>8)&255;rgba[i*4+2]=(c>>>16)&255;
 }
}
function frameStats(rgba,W,H){
 let min=255,max=0,before=0;const levels=new Set();
 for(let i=0;i<W*H;i++){const a=rgba[i*4+3];levels.add(a);if(a<min)min=a;if(a>max)max=a;if(a>0)before++;}
 const comps=keepLargest(rgba,W,H);
 const subject=comps.length?comps[0]:0;
 const dropped=before-subject;
 let xs=[],ys=[];
 for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(rgba[(y*W+x)*4+3]>0){xs.push(x);ys.push(y);}
 const bbox=xs.length?[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)]:null;
 return {alphaLevels:[...levels].sort((a,b)=>a-b),alphaMin:min,alphaMax:max,subject,components:1,
  componentsBefore:comps.length,componentSizesBefore:comps.slice(0,8),droppedPixels:dropped,
  preFilterOutside:dropped,bbox};
}
function diffPixels(a,b,W,H){
 let n=0;for(let i=0;i<W*H;i++){
  const j=i*4;
  if(a[j+3]!==b[j+3]||a[j]!==b[j]||a[j+1]!==b[j+1]||a[j+2]!==b[j+2])n++;
 }
 return n;
}

const exports=[];
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=4,rows=1;
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[],frames=[];
 let prev=null;
 for(let i=0;i<spec.n;i++){
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  p.lightK=.35;
  spec.draw(p,ph,i,spec.W,spec.H);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  quantize(rgba,spec.W,spec.H,spec.pal);
  const st=frameStats(rgba,spec.W,spec.H);
  if(st.droppedPixels>Math.max(100,Math.floor(st.subject*0.05)))throw Error(`${id} 第 ${i} 帧主体外像素过多：${st.droppedPixels}/${st.subject} ${st.componentSizesBefore}`);
  if(st.alphaMin!==0||st.alphaMax!==255)throw Error(`${id} 第 ${i} 帧 Alpha 未硬化：${st.alphaLevels}`);
  const [x0,y0,x1,y1]=st.bbox;
  if(spec.xEdges){
   if(y0<2||y1>spec.H-3)throw Error(`${id} 第 ${i} 帧触上下边：${st.bbox}`);
  }else if(x0<1||y0<1||x1>spec.W-2||y1>spec.H-2)throw Error(`${id} 第 ${i} 帧触边：${st.bbox}`);
  const changed=prev?diffPixels(prev,rgba,spec.W,spec.H):0;
  if(prev&&changed<Math.max(12,Math.floor(st.subject*0.01)))throw Error(`${id} 帧 ${i} 相位变化过小：${changed}/${st.subject}`);
  prev=rgba;
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);
  hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
  frames.push({index:i,phase:ph,sha256:SHA(png),alpha:st.alphaLevels,subject:st.subject,components:st.components,componentsBefore:st.componentsBefore,componentSizes:st.componentSizes,componentSizesBefore:st.componentSizesBefore,droppedPixels:st.droppedPixels,bbox:st.bbox,changed_pixels_vs_prev:changed});
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,kind:spec.layer,n:spec.n,W:spec.W,H:spec.H,AX:spec.AX,AY:spec.AY,loop:!!spec.loop,cols,rects,phase_png_sha256:hashes,atlas_sha256:SHA(png),frames});
}

// Q 蓄气三态：9/24/9 帧，384×256，根点在脚底。
for(const [state,count] of [['charge_start',9],['charge',24],['charge_stop',9]]){
 const id=`justice_fx_q_${state}`,folder=join(OUT,id);mkdirSync(folder);
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(QW*cols*QH*rows*4),rects=[],hashes=[],frames=[];
 let prev=null;
 for(let i=0;i<count;i++){
  const env=state==='charge_start'?(i+1)/count:state==='charge_stop'?Math.max(0.16,(count-1-i)/(count-1)):1;
  const t=i+(state==='charge'?9:state==='charge_stop'?33:0);
  const frame=createFrame(QW,QH),p=painterFor(frame).place(QAX,QAY);
  p.lightK=.35;
  drawCharge(p,t,env,i);
  const rgba=composite(frame,new Uint8ClampedArray(QW*QH*4),null);
  quantize(rgba,QW,QH,CHARGE);
  const st=frameStats(rgba,QW,QH);
  if(st.droppedPixels>Math.max(100,Math.floor(st.subject*0.05)))throw Error(`${id} 第 ${i} 帧主体外像素过多：${st.droppedPixels}/${st.subject} ${st.componentSizesBefore}`);
  if(st.alphaMin!==0||st.alphaMax!==255)throw Error(`${id} 第 ${i} 帧 Alpha 未硬化：${st.alphaLevels}`);
  const [x0,y0,x1,y1]=st.bbox;
  if(x0<2||y0<2||x1>QW-3||y1>QH-3)throw Error(`${id} 第 ${i} 帧触边：${st.bbox}`);
  const changed=prev?diffPixels(prev,rgba,QW,QH):0;
  if(prev&&changed<Math.max(12,Math.floor(st.subject*0.006)))throw Error(`${id} 帧 ${i} 相位变化过小：${changed}/${st.subject}`);
  prev=rgba;
  const x=i%cols*QW,y=Math.floor(i/cols)*QH;
  for(let row=0;row<QH;row++)atlas.set(rgba.subarray(row*QW*4,(row+1)*QW*4),((y+row)*QW*cols+x)*4);
  const png=encodePNG(QW,QH,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);
  hashes.push(SHA(png));rects.push([x,y,QW,QH]);
  frames.push({index:i,env,sha256:SHA(png),alpha:st.alphaLevels,subject:st.subject,components:st.components,componentsBefore:st.componentsBefore,componentSizes:st.componentSizes,componentSizesBefore:st.componentSizesBefore,droppedPixels:st.droppedPixels,bbox:st.bbox,changed_pixels_vs_prev:changed});
 }
 const png=encodePNG(QW*cols,QH*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,state,kind:'charge',n:count,W:QW,H:QH,AX:QAX,AY:QAY,loop:state==='charge',behind:true,cols,rects,phase_png_sha256:hashes,atlas_sha256:SHA(png),frames});
}

writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.justice-fx-family.v1',character:'ultraman-justice',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license:'MIT',license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length}));
