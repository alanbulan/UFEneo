// PixelFX 离线烘焙：奥特之父专属运行时特效家族。
// 原创绘制函数，不读取赛罗/泰罗/共享特效图集，也不烘焙任何人物整帧。
// 色板按奥父红银配色（深红→朱红→暖白）与金色角部光束；每帧硬 Alpha，主体单连通。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=20261112;
const SHA=b=>createHash('sha256').update(b).digest('hex');
const TAU=Math.PI*2;
// 奥父红银：深红甲、亮朱红、暖白须发/银甲高光、纯白亮芯。
const RED=fit(['#160406','#3a0910','#6a101a','#9c1c26','#cc3030','#f06048','#f6c4ac','#ffffff'],8);
// 金色角部光束与光轮用色。
const GOLD=fit(['#1a0c02','#402006','#7c3e0a','#b87414','#e6a62a','#ffd45c','#fff0b0','#ffffff'],8);

const rot=(x,y,a)=>[x*Math.cos(a)-y*Math.sin(a),x*Math.sin(a)+y*Math.cos(a)];
function thickPolyline(p,pts,width,c,a=1){
 for(let i=1;i<pts.length;i++)p.beam(pts[i-1][0],pts[i-1][1],pts[i][0],pts[i][1],width,c,a);
}
// 主体单连通保险：把任何游离小连通块用 1px 折线接到最大块，避免硬门主体外 alpha≥200。
function bridgeComponents(frame,color){
 const W=frame.w,H=frame.h,C=frame.color,N=W*H;
 const mask=new Uint8Array(N);for(let i=0;i<N;i++)mask[i]=C[i]!==0?1:0;
 const lab=new Int32Array(N);let count=0;const sizes=[];const stack=[];
 for(let i=0;i<N;i++){
  if(!mask[i]||lab[i])continue;
  count++;let n=0;stack.push(i);lab[i]=count;
  while(stack.length){
   const j=stack.pop();n++;const x=j%W,y=(j/W)|0;
   if(x>0){const k=j-1;if(mask[k]&&!lab[k]){lab[k]=count;stack.push(k);}}
   if(x<W-1){const k=j+1;if(mask[k]&&!lab[k]){lab[k]=count;stack.push(k);}}
   if(y>0){const k=j-W;if(mask[k]&&!lab[k]){lab[k]=count;stack.push(k);}}
   if(y<H-1){const k=j+W;if(mask[k]&&!lab[k]){lab[k]=count;stack.push(k);}}
  }
  sizes.push(n);
 }
 if(count<=1)return 0;
 let main=1;for(let i=2;i<=count;i++)if(sizes[i-1]>sizes[main-1])main=i;
 const mainPts=[];for(let i=0;i<N;i++)if(lab[i]===main)mainPts.push(i);
 for(let comp=1;comp<=count;comp++){
  if(comp===main)continue;
  let best=null,bestD=Infinity;
  for(let i=0;i<N;i++)if(lab[i]===comp){
   const x=i%W,y=(i/W)|0;
   for(const m of mainPts){const mx=m%W,my=(m/W)|0,d=Math.abs(x-mx)+Math.abs(y-my);if(d<bestD){bestD=d;best=[x,y,mx,my];}}
  }
  if(!best)continue;
  const[x1,y1,x2,y2]=best;
  let x=x1;while(x!==x2){C[y1*W+x]=color;x+=x2>x1?1:-1;}
  let y=y1;while(y!==y2){C[y*W+x2]=color;y+=y2>y1?1:-1;}
  C[y2*W+x2]=color;
  return 1+bridgeComponents(frame,color);
 }
 return 0;
}

// ---------- 掌弹：红银力量球，披风状尾焰 ----------
function pulseFlight(p,ph){
 const P=RED;
 for(let k=0;k<3;k++){
  const y=(k-1)*6+Math.sin(ph*TAU*2+k*1.4)*2;
  const L=14+5*Math.sin(ph*TAU*3+k*2.1);
  p.poly([[-3,y-3],[-L,y-4+Math.sin(ph*TAU*2+k)*2],[-L+4,y],[-L,y+4+Math.sin(ph*TAU*2+k)*2],[-3,y+3]],P[2+(k%2)]);
 }
 for(let k=0;k<3;k++){
  const a0=-1.0+k*TAU/3+ph*0.55,a1=a0+1.3;
  p.arc(0,0,12,5,a0,a1,(v)=>v<0.32?P[4]:v<0.7?P[5]:P[6]);
 }
 for(let k=0;k<4;k++){
  const a=ph*TAU+k*TAU/4;
  const len=17+3*Math.sin(ph*TAU*2+k*1.8);
  p.beam(Math.cos(a)*9,Math.sin(a)*9,Math.cos(a)*len,Math.sin(a)*len,2,(u)=>u<0.4?P[7]:P[4]);
 }
 p.circle(0,0,9,(d)=>d<0.3?P[7]:d<0.6?P[6]:d<0.85?P[4]:P[3]);
 p.circle(-1,0,4,P[7]);
}

// ---------- 力量爆：亮芯 + 十向披风状火舌 + 旋转光轮 ----------
function powerBurst(p,ph,R){
 const P=RED,grow=0.35+0.65*Math.min(1,ph*1.7),r0=R*0.42*grow;
 for(let i=0;i<10;i++){
  const a=i*TAU/10+ph*0.65;
  const len=r0*(1.45+0.6*Math.sin(ph*TAU*3+i*1.9));
  p.beam(0,0,Math.cos(a)*len,Math.sin(a)*len,3,(u)=>u<0.42?P[7]:i%2?P[5]:P[6]);
  const bx=Math.cos(a)*len*0.62,by=Math.sin(a)*len*0.62,b=a+0.55*(i%2?1:-1);
  p.beam(bx,by,bx+Math.cos(b)*len*0.33,by+Math.sin(b)*len*0.33,2,P[4]);
 }
 for(let k=0;k<2;k++){
  const rr=r0*(1.05+k*0.32),w=3-k;
  p.ring(0,0,rr,w,(v,ang)=>Math.sin(ang*4+ph*TAU*2+k)>0.15?(v>0.5?P[7]:P[5]):P[2]);
 }
 p.circle(0,0,r0*0.55,(d)=>d<0.35?P[7]:d<0.7?P[6]:P[5]);
 p.circle(0,0,r0*0.24,P[7]);
}

// ---------- 力量光束：暖白主芯、红甲层、银须锯齿缘与推进式披风焰 ----------
function powerBeam(p,len,thick,P,ph){
 const half=thick*0.5;
 for(let x=0;x<=len;x++){
  const taper=Math.min(1,(x+6)/14)*Math.min(1,(len-x)/20+0.35);
  const wave=1+0.06*Math.sin(x*0.22-ph*TAU*5);
  const band=Math.abs(x-(ph*len*1.35)%len)<28;
  const h=Math.max(1,Math.floor(half*taper*wave));
  for(let y=-h;y<=h;y++){
   const q=Math.abs(y)/h;
   let lv=q<0.16?7:q<0.34?6:q<0.55?5:q<0.74?4:q<0.9?3:2;
   if(band&&q<0.55)lv=Math.min(7,lv+2);
   p.px(x,y,P[lv]);
  }
  // 上下银须/披风锯齿：短焰从束身伸出，与束身相连。
  if((x%11+Math.round(ph*11))%11<4){
   const e=1+2+((x*7)%3);
   p.beam(x,-h,x+1,-h-e,2,P[3]);
   p.beam(x,h,x+1,h+e,2,P[3]);
   p.px(x+1,-h-e,P[6]);p.px(x+1,h+e,P[6]);
  }
  // 每 36px 一组向前推进的 V 形角纹。
  const vx=Math.round(x+ph*36)%36;
  if(vx<3){
   for(let d=0;d<=h;d+=1){
    p.px(x,h-d,P[7]);p.px(x,-h+d,P[7]);
   }
  }
 }
 // 枪口：短十字焰，仍与束身相接。
 for(let y=-half-8;y<=half+8;y++)p.px(0,y,Math.abs(y)<half?P[7]:P[4]);
 for(let x=-6;x<=6;x++)p.px(x,0,P[7]);
 p.circle(0,0,half*0.5,(d)=>d<0.35?P[7]:P[6]);
 // 束端：角形刃尖与回卷披风尾，和束身相连。
 for(let d=0;d<=10;d++){
  const hh=Math.max(1,Math.floor(half*(1-d/10)));
  for(let y=-hh;y<=hh;y++)p.px(len+d,y,P[y===0?7:5]);
 }
 for(let d=0;d<=12;d+=2){
  p.beam(len-6-d,0,len-2-d,-half-6-d*0.4,2,P[3]);
  p.beam(len-6-d,0,len-2-d,half+6+d*0.4,2,P[3]);
 }
 p.circle(len,0,3,P[7]);
}

// ---------- 月牙弹：红银新月刃 + 披风尾 ----------
function arrowFlight(p,ph){
 const P=RED,wob=Math.sin(ph*TAU)*1.8;
 p.poly([[13,0],[-17,-6+wob],[-6,0],[-19,7+wob],[12,3]],P[3]);
 p.poly([[12,-1],[-8,-4+wob],[-2,-1],[-9,3+wob],[12,1]],P[4]);
 p.arc(0,0,20,6,-1.12,1.12,(v)=>v<0.3?P[7]:v<0.65?P[6]:P[4]);
 p.arc(0,0,14,3,-0.9,0.9,P[1]);
 p.arc(0,0,21,2,-0.98,0.98,P[7]);
 const tip=1.12;
 for(const s of [-1,1]){
  const bx=Math.cos(s*tip)*20,by=Math.sin(s*tip)*20;
  p.beam(bx,by,bx+4,by+s*7,3,(u)=>u<0.45?P[7]:P[5]);
 }
 p.circle(12,0,4,(d)=>d<0.5?P[7]:P[5]);
}

// ---------- 月牙命中：弧刃爆裂 ----------
function arrowHit(p,ph){
 const P=RED,grow=0.4+0.6*Math.min(1,ph*1.8);
 p.arc(0,0,34*grow,5,-1.15,1.15,(v)=>v>0.55?P[7]:P[5]);
 p.arc(0,0,26*grow,4,-0.95,0.95,P[6]);
 for(let i=0;i<7;i++){
  const a=-1.1+i*0.36+ph*0.4,len=26*grow*(1+0.4*Math.sin(ph*TAU*3+i));
  p.beam(0,0,Math.cos(a)*len,Math.sin(a)*len,3,(u)=>u<0.4?P[7]:P[4]);
 }
 p.circle(0,0,9*grow,(d)=>d<0.4?P[7]:d<0.7?P[6]:P[5]);
 p.circle(0,0,4*grow,P[7]);
}

// ---------- 螺旋冲撞：角形力量钻 ----------
function spiralFlight(p,ph){
 const P=RED;
 p.poly([[38,0],[-14,-9],[-20,-4],[-20,4],[-14,9]],(x,y)=>Math.abs(y)<3?(x>20?P[7]:P[6]):Math.abs(y)<6?P[5]:P[3]);
 for(const s of [-1,1]){
  for(const off of [0,1]){
   const pts=[];
   for(let x=-14;x<=34;x+=2)pts.push([x,s*(6+2.2*Math.sin(x*0.33-ph*TAU*2))+s*off]);
   thickPolyline(p,pts,2,off?P[7]:P[5]);
  }
 }
 for(const s of [-1,1]){
  p.beam(-16,s*4,-27,s*13+Math.sin(ph*TAU*2)*2,4,(u)=>u<0.5?P[5]:P[3]);
  p.beam(-24,s*11,-29,s*7,2,P[6]);
 }
 p.poly([[-18,-5],[-24,0],[-18,5]],P[4]);
 p.circle(34,0,3,(d)=>d<0.5?P[7]:P[6]);
}

// ---------- 螺旋命中：角钻贯穿爆 ----------
function spiralHit(p,ph){
 const P=RED,grow=0.38+0.62*Math.min(1,ph*1.8),r0=36*grow;
 for(let i=0;i<8;i++){
  const a=i*TAU/8+ph*0.5,len=r0*(1.25+0.35*Math.sin(ph*TAU*3+i*2));
  p.beam(0,0,Math.cos(a)*len,Math.sin(a)*len,3,(u)=>u<0.4?P[7]:P[5]);
  const b=a+0.4;
  p.beam(Math.cos(a)*len*0.6,Math.sin(a)*len*0.6,Math.cos(a)*len*0.6+Math.cos(b)*len*0.3,Math.sin(a)*len*0.6+Math.sin(b)*len*0.3,2,P[4]);
 }
 p.ring(0,0,r0*0.8,3,(v,ang)=>Math.sin(ang*3+ph*TAU*2)>0?(v>0.5?P[7]:P[5]):P[2]);
 p.ring(0,0,r0*0.45,3,P[6]);
 for(let i=0;i<3;i++){
  const a=ph*TAU+i*TAU/3;
  p.beam(Math.cos(a)*r0*0.15,Math.sin(a)*r0*0.15,Math.cos(a)*r0*0.78,Math.sin(a)*r0*0.78,2,P[6]);
 }
 p.circle(0,0,7,(d)=>d<0.4?P[7]:P[5]);
}

// ---------- 奥特光轮：角形光轮（外轮三刃 + 内轮轮辐） ----------
function ringsFlight(p,ph){
 const P=GOLD,spin=ph*TAU/3;
 p.ring(0,0,30,4,(v,ang)=>Math.sin(ang*3+spin*3)>0.25?(v>0.5?P[7]:P[5]):P[3]);
 p.ring(0,0,16,3,(v)=>v>0.4?P[6]:P[4]);
 p.circle(0,0,7,(d)=>d<0.4?P[7]:P[6]);
 for(let i=0;i<3;i++){
  const a=spin+i*TAU/3;
  const x0=Math.cos(a)*14,y0=Math.sin(a)*14,x1=Math.cos(a)*40,y1=Math.sin(a)*40;
  p.beam(x0,y0,x1,y1,4,(u)=>u<0.4?P[7]:P[4]);
  p.beam(x1,y1,x1+Math.cos(a+0.5)*8,y1+Math.sin(a+0.5)*8,2,P[5]);
  p.beam(x1,y1,x1+Math.cos(a-0.5)*8,y1+Math.sin(a-0.5)*8,2,P[5]);
 }
 for(let i=0;i<3;i++){
  const a=spin+i*TAU/3+0.5;
  p.beam(Math.cos(a)*5,Math.sin(a)*5,Math.cos(a)*17,Math.sin(a)*17,2,P[5]);
 }
}

// ---------- 光轮命中：三重角环爆 ----------
function ringsHit(p,ph){
 const P=GOLD,grow=0.4+0.6*Math.min(1,ph*1.7);
 for(let k=0;k<3;k++){
  const rr=16+k*10*grow,w=3;
  p.ring(0,0,rr,w,(v,ang)=>Math.sin(ang*(3+k)+ph*TAU*2)>0?(v>0.5?P[7]:P[5]):P[3]);
 }
 for(let i=0;i<6;i++){
  const a=i*TAU/6+ph*0.35,len=34*grow*(1+0.25*Math.sin(ph*TAU*3+i));
  p.beam(0,0,Math.cos(a)*len,Math.sin(a)*len,3,(u)=>u<0.45?P[7]:P[4]);
 }
 p.circle(0,0,8*grow,(d)=>d<0.4?P[7]:P[6]);
}

// ---------- 奥特屏障：红银披风编织光壁 ----------
function barrier(p,ph,idx){
 const P=RED,pulse=ph+(idx%3)*0.18,L=-38,R=38,T=-72,B=72;
 for(const sx of [L+3,R-3]){
  const pts=[];for(let y=T;y<=B;y+=4)pts.push([sx+Math.sin(y*0.09+pulse*TAU)*2.2,y]);
  thickPolyline(p,pts,5,P[4]);
 }
 for(const sy of [T+2,B-2]){
  const pts=[];for(let x=L;x<=R;x+=4)pts.push([x,sy+Math.sin(x*0.1-pulse*TAU)*1.5]);
  thickPolyline(p,pts,5,P[4]);
 }
 for(let k=0;k<5;k++){
  const sx=L+10+k*14,pts=[];
  for(let y=T+4;y<=B-4;y+=4)pts.push([sx+Math.sin(y*0.11+pulse*TAU+k*0.9)*3,y]);
  thickPolyline(p,pts,3,k%2?P[5]:P[3]);
 }
 for(let k=0;k<2;k++){
  const sy=-24+k*48,pts=[];
  for(let x=L+2;x<=R-2;x+=4)pts.push([x,sy+Math.sin(x*0.16+pulse*TAU*1.3+k)*4]);
  thickPolyline(p,pts,2,P[6]);
 }
 p.ring(0,0,14,4,(v)=>v>0.5?P[6]:P[5]);
 p.poly([[0,-12],[12,0],[0,12],[-12,0]],(x,y)=>Math.abs(x)+Math.abs(y)<6?P[7]:P[5]);
 for(let i=0;i<4;i++){
  const a=i*TAU/4;
  p.beam(Math.cos(a)*10,Math.sin(a)*10,Math.cos(a)*(i%2?32:36),Math.sin(a)*(i%2?32:36),2,P[4]);
 }
}

// ---------- 父亲光轮抓取环（前后两层）：角焰光环 ----------
function catchRing(p,ph,part){
 const P=RED,cy=-56,R=42,spin=ph*TAU*0.25;
 if(part==='back'){
  p.arc(0,cy,R,5,Math.PI*0.55,Math.PI*1.45,(v,ang)=>v>0.55?P[6]:P[4]);
  p.arc(0,cy,33,3,Math.PI*0.62,Math.PI*1.38,P[6]);
  for(let k=0;k<3;k++){
   const a=Math.PI*0.7+k*0.55;
   const x0=Math.cos(a)*R,y0=cy+Math.sin(a)*R;
   const x1=Math.cos(a)*(R+11+3*Math.sin(ph*TAU*2+k)),y1=cy+Math.sin(a)*(R+11+3*Math.sin(ph*TAU*2+k));
   p.beam(x0,y0,x1,y1,4,(u)=>u<0.5?P[5]:P[3]);
   p.beam(x1,y1,x1+Math.cos(a+0.5)*7,y1+Math.sin(a+0.5)*7,2,P[6]);
  }
  for(let k=0;k<3;k++){
   const a=Math.PI*0.72+k*0.52;
   p.beam(Math.cos(a)*33,cy+Math.sin(a)*33,Math.cos(a)*R,cy+Math.sin(a)*R,2,P[5]);
  }
 }else{
  p.arc(0,cy,R,5,-Math.PI*0.45,Math.PI*0.45,(v,ang)=>v>0.55?P[7]:P[5]);
  p.arc(0,cy,33,3,-Math.PI*0.4,Math.PI*0.4,P[6]);
  for(let k=0;k<2;k++){
   const a=-Math.PI*0.25+k*Math.PI*0.5;
   const x0=Math.cos(a)*R,y0=cy+Math.sin(a)*R;
   const x1=Math.cos(a)*(R+10+3*Math.sin(ph*TAU*2+k)),y1=cy+Math.sin(a)*(R+10+3*Math.sin(ph*TAU*2+k));
   p.beam(x0,y0,x1,y1,4,(u)=>u<0.5?P[7]:P[4]);
   p.beam(x1,y1,x1+Math.cos(a-0.5)*6,y1+Math.sin(a-0.5)*6,2,P[6]);
  }
  for(let k=0;k<2;k++){
   const a=-Math.PI*0.3+k*Math.PI*0.6;
   p.beam(Math.cos(a)*33,cy+Math.sin(a)*33,Math.cos(a)*R,cy+Math.sin(a)*R,2,P[5]);
  }
 }
}

// ---------- Q 蓄气：周身椭圆火焰环（9/24/9 帧） ----------
const QW=384,QH=256,QAX=192,QAY=246;
// 蓄气专用火焰色板：深红→朱红→橙→橙白→白；外焰只取低段，亮芯与火星取高段。
const QFIRE=fit(['#120304','#38070c','#681018','#9a1c26','#cc3030','#f25a34','#ff9a2e','#ffe6a0','#ffffff'],9);
function chargeFlame(ph,env){
 const frame=createFrame(QW,QH),p=painterFor(frame).place(QAX,QAY),F=QFIRE;
 const cx=0,cy=-92,rx=10+62*env,ry=12+72*env,TAU2=TAU;
 const wob=(a,k)=>1+k*(0.035*Math.sin(a*5+ph*TAU2*2)+0.022*Math.sin(a*9-ph*TAU2*3)+0.012*Math.sin(a*15+ph*TAU2*4));
 const at=(a,r)=>{const w=wob(a,1);return [cx+Math.cos(a)*rx*w*r,cy+Math.sin(a)*ry*w*r];};
 // 宽火舌：填成水滴形，底宽顶尖，带卷曲与内侧亮纹。
 const tongue=(bx,by,dx,dy,L,wb,deep,mid,bright,curl,seed)=>{
  const dn=Math.hypot(dx,dy);dx/=dn;dy/=dn;
  const tx=-dy,ty=dx,cs=[];
  for(let s=0;s<=1.0001;s+=0.1){
   const bend=(curl*Math.sin(s*Math.PI*0.9)+0.9*Math.sin(s*Math.PI*2+seed))*s*L*0.45;
   cs.push([bx+dx*L*s+tx*bend,by+dy*L*s+ty*bend]);
  }
  const edge=[];
  for(let j=0;j<cs.length;j++){
   const s=j/(cs.length-1),w=Math.max(1.2,wb*Math.pow(1-s,0.62)*(1+0.16*Math.sin(s*7.3+seed*2.1)));
   edge.push([cs[j][0]+tx*w,cs[j][1]+ty*w]);
  }
  for(let j=cs.length-1;j>=0;j--){
   const s=j/(cs.length-1),w=Math.max(1.2,wb*Math.pow(1-s,0.62)*(1+0.16*Math.sin(s*7.3+seed*2.1)));
   edge.push([cs[j][0]-tx*w,cs[j][1]-ty*w]);
  }
  p.poly(edge,deep);
  // 沿中轴再落一道实心笔画，保证根部到尖端连续，避免薄多边形落空产生游离块。
  thickPolyline(p,cs,Math.max(2,Math.round(wb*1.1)),deep);
  const inner=cs.slice(1,Math.max(2,Math.round(cs.length*0.62)));
  thickPolyline(p,inner,Math.max(1,Math.round(wb*0.34)),(u)=>u<0.5?mid:bright);
  p.circle(cs[cs.length-1][0],cs[cs.length-1][1],Math.max(1,wb*0.2),(d)=>d<0.6?bright:mid);
 };
 // 火焰轮廓：外缘叠加多个尖峰，形成向上偏的环状火舌剪影，而不是等宽圆环。
 const TIPS=11;
 const spike=(a)=>{
  let h=0;
  for(let k=0;k<TIPS;k++){
   const ak=TAU2*k/TIPS+0.13*Math.sin(ph*TAU2*2+k*1.7);
   let d=a-ak;d=Math.atan2(Math.sin(d),Math.cos(d));
   const w=0.065+0.025*Math.abs(Math.sin(k*2.3+ph*TAU2*3));
   const amp=(0.26+0.28*Math.abs(Math.sin(ph*TAU2*2+k*2.1)))*Math.pow((1-Math.sin(a))/2,0.85);
   const t=Math.max(0,1-Math.abs(d)/w);
   h=Math.max(h,amp*Math.pow(t,1.7));
  }
  return h*env;
 };
 const rOutAt=(a)=>1.0+spike(a);
 const rInAt=(a)=>0.66+0.03*Math.sin(a*3+ph*TAU2*2)+0.02*Math.sin(a*7-ph*TAU2*3);
 // 1) 环状火身：径向分层（内橙→朱红→深红），外缘为尖峰火舌剪影。
 const BANDS=[[0,0.34,F[6]],[0.34,0.62,F[5]],[0.62,0.86,F[4]],[0.86,1,F[3]]];
 for(let i=0;i<192;i++){
  const a0=TAU2*i/192,a1=TAU2*(i+1)/192;
  const r0=rInAt(a0),r1=rInAt(a1),ro0=rOutAt(a0),ro1=rOutAt(a1);
  for(const[lo,hi,color]of BANDS){
   const k0=r0+(ro0-r0)*lo,k1=r1+(ro1-r1)*lo,k2=r0+(ro0-r0)*hi,k3=r1+(ro1-r1)*hi;
   const[ix,iy]=at(a0,k0),[jx,jy]=at(a1,k1),[ox,oy]=at(a0,k2),[px,py]=at(a1,k3);
   const tone=lo>=0.78&&(i%9<3)?F[1]:color;
   p.poly([[ix,iy],[ox,oy],[px,py],[jx,jy]],tone);
  }
 }
 // 1b) 尖峰火舌尖端：在每处峰顶补一条向上偏的亮红外焰，尖端橙点。
 for(let k=0;k<TIPS;k++){
  const ak=TAU2*k/TIPS+0.13*Math.sin(ph*TAU2*2+k*1.7);
  const amp=spike(ak);
  if(amp<0.05)continue;
  const[bx,by]=at(ak,0.95);
  const L=amp*ry*0.9;
  tongue(bx,by,Math.cos(ak),Math.sin(ak)-0.5,L,4+2.5*Math.abs(Math.sin(ph*TAU2*2+k*2.1)),F[2],F[4],F[5],(k%2?1:-1)*0.45,k*1.9);
 }
 // 2) 内缘火舌：短而宽的橙色火舌从火环内缘朝中心卷出，环内保持通透。
 for(let i=0;i<8;i++){
  const a=TAU2*i/8+0.13*Math.sin(ph*TAU2*2+i*1.5);
  const L=(9+13*Math.abs(Math.sin(ph*TAU2*3+i*1.8)))*env;
  const[bx,by]=at(a,0.68);
  tongue(bx,by,-Math.cos(a),-Math.sin(a)+0.4,L,3+2*Math.abs(Math.sin(i*1.7+ph*TAU2*2)),F[4],F[4],F[5],(i%2?1:-1)*0.7,i*2.3);
 }
 // 4) 橙白亮芯：中心火团、宽短焰与白色核点。
 const cr=Math.max(5,(9+16*env+5*Math.sin(ph*TAU2*3))*Math.min(1,env+0.45));
 p.circle(cx,cy,cr,(d)=>d<0.26?F[8]:d<0.46?F[7]:d<0.66?F[6]:d<0.86?F[5]:F[4]);
 for(let i=0;i<7;i++){
  const a=TAU2*i/7+ph*0.9,L=cr*(1.25+0.8*Math.abs(Math.sin(ph*TAU2*3+i*1.7)));
  tongue(cx+Math.cos(a)*cr*0.5,cy+Math.sin(a)*cr*0.5,Math.cos(a),Math.sin(a),L,3.2+1.6*Math.abs(Math.sin(i+ph*TAU2*2)),F[5],F[6],F[7],0.6,i*1.3);
 }
 p.circle(cx+1.6*Math.sin(ph*TAU2*5),cy+1.2*Math.cos(ph*TAU2*4),Math.max(1.4,cr*0.26),F[8]);
 // 5) 芯到火环的宽火柱：六条填实火舌从芯伸到火环内缘，把主体连成一块。
 for(let i=0;i<6;i++){
  const a=TAU2*i/6+0.35+ph*TAU2*0.22;
  const[ex,ey]=at(a,0.72);
  const sxp=cx+Math.cos(a)*cr*0.6,syp=cy+Math.sin(a)*cr*0.6;
  const reach=0.55+0.45*Math.abs(Math.sin(ph*TAU2*2+i*1.6));
  tongue(sxp,syp,(ex-sxp)*reach,(ey-syp)*reach,Math.hypot(ex-sxp,ey-syp)*reach,3.6+1.6*Math.sin(ph*TAU2*2+i*2.2),F[2],F[4],F[5],0.5,i*0.9);
 }
 // 6) 向上升腾的火星：S 形卷曲火线连回火环上缘，头部橙白，随相位上行。
 const SP=5;
 for(let k=0;k<SP;k++){
  const a=-Math.PI/2+(k-(SP-1)/2)*0.3+0.06*Math.sin(ph*TAU2*2+k*1.3);
  const[bx0,by0]=at(a,0.96);
  const u=(k/SP+ph*2)%1,rise=(8+30*u)*env;
  const drift=Math.sin(ph*TAU2*3+k*2.2)*5+(k-(SP-1)/2)*10;
  const hx=bx0+drift,hy=by0-rise;
  const pts=[];
  for(let s=0;s<=1.001;s+=0.2){
   const swing=Math.sin(s*Math.PI*1.6+ph*TAU2*4+k*1.7)*4*s;
   pts.push([bx0+(hx-bx0)*s+swing,by0+(hy-by0)*s]);
  }
  thickPolyline(p,pts,2,(uu)=>uu<0.55?F[3]:F[5]);
  p.circle(hx,hy,2.4,(d)=>d<0.4?F[8]:d<0.7?F[7]:F[6]);
  p.px(hx+1,hy-2,F[6]);
 }
 const bridged=bridgeComponents(frame,F[4]);
 return [composite(frame,new Uint8ClampedArray(QW*QH*4),null),bridged];
}

// ---------- 段规格 ----------
const SPECS={
 'father_fx_pulse_flight':{n:4,W:64,H:64,AX:32,AY:32,loop:true,layer:'flight',pal:RED,draw:pulseFlight},
 'father_fx_pulse_hit':{n:4,W:96,H:96,AX:48,AY:48,layer:'impact',pal:RED,draw:(p,ph)=>powerBurst(p,ph,40)},
 'father_fx_beam':{n:4,W:420,H:96,AX:0,AY:48,loop:true,layer:'beam',pal:RED,draw:(p,ph)=>powerBeam(p,410,44,RED,ph)},
 'father_fx_beam_hit':{n:4,W:104,H:104,AX:52,AY:52,layer:'impact',pal:RED,draw:(p,ph)=>powerBurst(p,ph,44)},
 'father_fx_arrow_flight':{n:4,W:64,H:64,AX:32,AY:32,loop:true,layer:'flight',pal:RED,draw:arrowFlight},
 'father_fx_arrow_hit':{n:4,W:96,H:96,AX:48,AY:48,layer:'impact',pal:RED,draw:arrowHit},
 'father_fx_spiral':{n:4,W:96,H:96,AX:48,AY:48,loop:true,layer:'flight',pal:RED,draw:spiralFlight},
 'father_fx_spiral_hit':{n:4,W:96,H:96,AX:48,AY:48,layer:'impact',pal:RED,draw:spiralHit},
 'father_fx_rings':{n:4,W:128,H:128,AX:64,AY:64,loop:true,layer:'flight',pal:GOLD,draw:ringsFlight},
 'father_fx_rings_hit':{n:4,W:96,H:96,AX:48,AY:48,layer:'impact',pal:GOLD,draw:ringsHit},
 'father_fx_barrier':{n:4,W:160,H:160,AX:80,AY:80,loop:true,layer:'guard',pal:RED,draw:barrier},
 'father_fx_catch_back':{n:4,W:128,H:128,AX:64,AY:125,layer:'catch',pal:RED,behind:true,draw:(p,ph)=>catchRing(p,ph,'back')},
 'father_fx_catch_front':{n:4,W:128,H:128,AX:64,AY:125,layer:'catch',pal:RED,behind:false,draw:(p,ph)=>catchRing(p,ph,'front')},
};
// ---------- 烘焙循环 ----------
const exports=[];
for(const[id,spec]of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];let bridged=0;
 for(let i=0;i<spec.n;i++){
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  spec.draw(p,ph,i,spec.W,spec.H,spec.AX,spec.AY);
  bridged+=bridgeComponents(frame,spec.pal[5]);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  for(let j=0;j<rgba.length;j+=4){
   if(rgba[j+3]<128){rgba.fill(0,j,j+4);continue;}
   rgba[j+3]=255;
  }
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,kind:spec.layer,n:spec.n,W:spec.W,H:spec.H,AX:spec.AX,AY:spec.AY,loop:!!spec.loop,behind:!!spec.behind,cols,rects,bridged,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
// Q 蓄气三态：9/24/9 帧，384×256，脚底锚 [192,246]。
for(const[state,count]of[['charge_start',9],['charge',24],['charge_stop',9]]){
 const id=`father_fx_q_${state}`,folder=join(OUT,id);mkdirSync(folder);
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(QW*cols*QH*rows*4),rects=[],hashes=[];let bridged=0;
 for(let i=0;i<count;i++){
  let env,ph;
  if(state==='charge_start'){const e=(i+1)/count;env=0.16+0.84*e*e;ph=i/count;}
  else if(state==='charge_stop'){const e=count>1?i/(count-1):1;env=0.12+0.88*Math.pow(1-e,1.15);ph=e;}
  else{ph=i/count;env=0.92+0.08*Math.sin(ph*TAU*2);}
  const[rgba,bridgeN]=chargeFlame(ph,env);
  bridged+=bridgeN;
  const x=i%cols*QW,y=Math.floor(i/cols)*QH;
  for(let row=0;row<QH;row++)atlas.set(rgba.subarray(row*QW*4,(row+1)*QW*4),((y+row)*QW*cols+x)*4);
  const png=encodePNG(QW,QH,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,QW,QH]);
 }
 const png=encodePNG(QW*cols,QH*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,state,kind:'charge',n:count,W:QW,H:QH,AX:QAX,AY:QAY,loop:state==='charge',behind:true,cols,rects,bridged,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.father-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length,bridged:exports.reduce((a,e)=>a+e.bridged,0)}));
