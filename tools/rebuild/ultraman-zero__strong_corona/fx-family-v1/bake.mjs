// PixelFX 离线烘焙：强壮日冕赛罗专属特效家族。
// 原创绘制函数，不读取他人角色特效图集；色板为日冕红金/火焰橙白，与赛罗默认青蓝区分。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=20261112^0xC0A0A;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
const TAU=Math.PI*2;
const CORONA=fit(['#1a0502','#4a0f06','#8a1b10','#cc3a14','#ff6a1e','#ffb020','#ffe8a0','#ffffff'],8);
const GOLD=fit(['#140a02','#402006','#7a3c08','#b86a10','#e6a020','#ffd060','#fff0b8','#ffffff'],8);
const EMER=fit(['#120602','#3a1208','#6a2210','#a04014','#d86a18','#ff9a30','#ffd0a0','#ffffff'],8);
const SLUG=fit(['#120804','#301408','#5a2810','#8a4420','#c86a30','#f0a060','#ffd8b8','#ffffff'],8);

function star(p,cx,cy,r,PAL,ph,spikes=6){
 const base=ph*TAU*0.3;
 for(let k=0;k<spikes;k++){
  const a=base+k*TAU/spikes;
  const len=r*(0.7+0.3*Math.sin(ph*TAU*3+k*1.9));
  p.line(cx,cy,cx+Math.cos(a)*len,cy+Math.sin(a)*len,(u)=>(u<0.4?PAL[7]:PAL[5]));
 }
 p.circle(cx,cy,r*0.24,PAL[6]);p.circle(cx,cy,r*0.12,PAL[7]);
}
function wideBeamBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const w=thick*0.5*(1+0.07*Math.sin(d*0.19-ph*TAU*5))*Math.min(1,(d+4)/10)*Math.min(1,(len-d)/18+0.3);
  const notch=((d*0.38-ph*len*0.55)%15+15)%15<4;
  for(let q0=-w*1.3;q0<=w*1.3;q0+=0.5){
   const qn=Math.abs(q0)/w;
   if(notch&&qn>0.88)continue;
   let lv=qn<0.1?7:qn<0.26?6:qn<0.48?5:qn<0.7?4:qn<0.9?3:2;
   p.px(d,q0,PAL[lv]);
  }
  for(const s of [-1,1]){
   const a=d*0.17-ph*TAU*3+s*Math.PI*0.5;
   const off=Math.sin(a)*w*1.2;
   if(Math.cos(a)>0.12)p.dot(d,off,Math.cos(a)>0.55?PAL[7]:PAL[5],0.8);
  }
  if(Math.round(d*2)%140===0){
   const l=(thick*0.5)*(1.0+0.45*Math.sin(ph*TAU*4+d*0.03));
   p.line(d,0,d,-l,PAL[6],0.85);p.line(d,0,d,l,PAL[6],0.85);
   p.dot(d,-l,PAL[7]);p.dot(d,l,PAL[7]);
  }
  if((Math.round(d*2)&15)===0)p.glow(d,0,w*2.0+3,PAL[5],0.11);
 }
 star(p,3,0,thick*0.5,CORONA,ph,6);
 p.circle(0,0,thick*0.22,PAL[6]);p.circle(0,0,thick*0.1,PAL[7]);
 p.glow(0,0,thick*0.85,PAL[6],0.65);
 const tip=thick*0.58;
 p.line(len,0,len+tip,0,PAL[7]);p.line(len,-tip*0.65,len,0,PAL[6]);p.line(len,tip*0.65,len,0,PAL[6]);
 for(let k=0;k<2;k++){
  const q=(((ph*2.2+k/2)%1)+1)%1;
  p.ring(len,0,3+14*q,Math.max(1,2*(1-q)),q<0.3?PAL[7]:PAL[5],1.05-q);
 }
 p.circle(len,0,tip*0.5,PAL[5]);p.circle(len,0,tip*0.28,PAL[7]);
 p.glow(len,0,thick*0.85,PAL[5],0.7);
}
function emeriumBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const w=thick*0.5*(1+0.06*Math.sin(d*0.28-ph*TAU*6))*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/16+0.3);
  for(let q0=-w*1.18;q0<=w*1.18;q0+=0.5){
   const qn=Math.abs(q0)/w;
   let lv=qn<0.18?7:qn<0.4?6:qn<0.66?5:qn<0.88?4:3;
   p.px(d,q0,PAL[lv]);
  }
  for(const s of [-1,1]){const off=Math.sin(d*0.22-ph*TAU*4+s)*w*1.08;if(Math.sin(d*0.22-ph*TAU*4+s)>0.18)p.dot(d,off,PAL[7],0.75);}
 }
 for(let k=0;k<4;k++){
  const cx=((k+ph)%4)*(len/4)+10;
  for(let a=-1.2;a<=1.2;a+=0.05){
   const r=thick*1.0+2.2*Math.sin(a*2.4+ph*TAU);
   const x=cx+Math.cos(a)*r*0.6,y=Math.sin(a)*r;
   p.disc(x,y,1.5,Math.abs(a)<0.5?PAL[7]:PAL[5],0.8);
  }
 }
 star(p,3,0,thick*0.48,EMER,ph,6);
 p.circle(0,0,thick*0.2,PAL[6]);p.circle(0,0,thick*0.1,PAL[7]);
 p.glow(0,0,thick*0.8,PAL[6],0.6);
 for(let a=-1.45;a<=1.45;a+=0.05){
  const r=thick*1.45;
  p.disc(len+Math.cos(a)*r*0.72,Math.sin(a)*r,1.4,Math.abs(a)<0.4?PAL[7]:PAL[6],0.85);
 }
 p.glow(len,0,thick*1.0,PAL[5],0.65);
}
function sluggerBlade(p,ph,PAL){
 const ang=ph*TAU*0.5-0.3;
 const ca=Math.cos(ang),sa=Math.sin(ang);
 const put=(x,y,c,a=1)=>p.disc(x*ca-y*sa,y*ca+x*sa,1.4,c,a);
 for(let a=-1.4;a<=1.4;a+=0.035){
  for(let r=8;r<=14;r+=0.6){
   const u=(r-8)/6;
   put(Math.cos(a)*r-2,Math.sin(a)*r,Math.abs(a)>1.12?PAL[7]:(u>0.6?PAL[6]:u>0.3?PAL[4]:PAL[3]),0.95);
  }
 }
 for(let a=-1.22;a<=1.22;a+=0.04)put(Math.cos(a)*14,Math.sin(a)*14,PAL[7],0.95);
 for(let a=-1.08;a<=1.08;a+=0.05)put(Math.cos(a)*9.4-2,Math.sin(a)*9.4,PAL[2],0.9);
 for(let k=0;k<2;k++){
  const a0=ph*TAU*1.6+k*Math.PI;
  for(let u=0;u<0.42;u+=0.04){const a=a0+u;put(Math.cos(a)*12.2,Math.sin(a)*12.2,u<0.18?PAL[7]:PAL[5],1-u*1.5);}
 }
 p.circle(0,0,2.2,PAL[7]);p.glow(0,0,10,PAL[6],0.32);
}
function sluggerTrail(p,ph,PAL){
 for(let d=0;d<132;d+=1){
  const u=d/132,x=-d,y=Math.sin(d*0.24-ph*TAU*2.6)*4.0*u;
  const lv=Math.max(3,Math.floor((1-u)*7));
  if(((d+Math.floor(ph*9))%3)<2){
   p.px(x,y,lv>=6?PAL[7]:PAL[lv]);
   if(u<0.6)p.px(x,y+1,PAL[Math.max(2,lv-2)]);
   if(u<0.35)p.px(x,y-1,PAL[Math.max(3,lv-1)]);
  }
  if(d%7===0)p.dot(x,y,PAL[6],0.65*(1-u));
  if(d%13===0)p.glow(x,y,3,PAL[5],0.1*(1-u));
 }
 p.circle(0,0,2.6,PAL[6]);p.circle(0,0,1.4,PAL[7]);p.glow(0,0,11,PAL[6],0.32);
}
function hitBurst(p,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12),k=1-ph,R0=R*0.42*grow;
 for(let i=0;i<10;i++){
  const a=i*TAU/10+ph*2.2,l=R0*(1.35+0.7*Math.sin(ph*TAU*5+i*1.6));
  p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.45?PAL[7]:i%2?PAL[6]:PAL[5]),(u)=>(u<0.5?1:1.5-u));
 }
 star(p,0,0,R0*0.85,PAL,ph,6);
 p.circle(0,0,R0*0.55,PAL[7],k);
 for(let i=0;i<3;i++){
  const q=(((ph*1.7+i/3)%1)+1)%1;
  p.ring(0,0,3+R*0.5*Math.pow(q,2),Math.max(1,2.2*(1-q)),q<0.3?PAL[7]:PAL[5],(1.1-q)*k);
 }
 p.glow(0,0,R*0.75,PAL[5],0.65*k);
 for(let j=0;j<12;j++){
  const a=hash(j*3+1)*TAU,sp=24+hash(j*7+2)*55,d0=ph*sp;
  const x=Math.cos(a)*d0,y=Math.sin(a)*d0-d0*d0*0.05,kk=1-ph;
  if(kk>0.12)p.disc(x,y,0.8+hash(j)*1.2,j%3?PAL[6]:PAL[7],kk*0.8);
 }
}
function catchFlash(p,ph,PAL){
 const k=1-ph;
 for(let i=0;i<3;i++){
  const q=(((ph*1.4+i/3)%1)+1)%1;
  p.ring(0,0,26*(1-q)+3,Math.max(1,2.2*(1-q)),q<0.35?PAL[7]:PAL[5],(1-q)*k*0.85);
 }
 for(let s=-1;s<=1;s+=2){
  for(let u=0;u<1;u+=0.04){
   const x=s*(4+u*9),y=-u*18+4;
   p.disc(x,y,u<0.2?PAL[7]:PAL[5],(1-u*0.5)*k*0.85);
  }
 }
 star(p,0,0,10*(0.6+0.4*k),PAL,ph,6);
 p.circle(0,0,3.0,PAL[7],k);p.glow(0,0,20,PAL[5],0.4*k);
}

const QW=384,QH=256,QAX=192,QAY=246,QRX=78,QRY=92,QCCY=-96;
function chargeAura(t,env){
 const frame=createFrame(QW,QH),p=painterFor(frame).place(QAX,QAY);
 p.lightK=.55;
 const time=t/60;
 for(let side=-1;side<=1;side+=2){
  for(let k=0;k<3;k++){
   const speed=0.32+k*0.08,phase=((time*speed+k*0.29+hash(side*7+k*13+1)*0.1)%1),len=0.58,GAP=0.08;
   for(let u=0;u<len;u+=0.004){
    const a=((phase+u)%1)*Math.PI*(1-2*GAP)+GAP*Math.PI;
    const x=side*QRX*Math.max(0.12,Math.sin(a))*(1+0.06*Math.sin(time*4+k));
    const y=QCCY+QRY*Math.cos(a);
    const head=1-u/len,tail=u/len;
    const envY=env*(0.45+0.55*(1-a/Math.PI));
    const lv=Math.min(7,Math.floor(head*head*9*envY));
    if(lv<=0)continue;
    const wob=Math.sin(time*9+k*2.2+u*20)*2.4,size=(0.6+head*2.3)*envY;
    p.disc(x+wob,y,size,CORONA[lv],Math.min(1,(0.85-tail*0.55)*envY+0.15));
    if(lv>=6){p.disc(x+wob,y,size*0.5,CORONA[7],0.85*envY);p.glow(x+wob,y,7+head*8,CORONA[5],0.13*envY);}
   }
  }
  for(let j=0;j<7;j++){
   const spd=0.24+hash(side*31+j*7+3)*0.18,ph=((time*spd+j*0.14+side*0.4)%1),th=ph*Math.PI;
   const x=side*QRX*Math.max(0.15,Math.sin(th))*0.9+(hash(j+side*11+9)-0.5)*10;
   const y=QCCY+QRY*Math.cos(th),k2=(0.4+0.6*Math.sin(ph*Math.PI))*env;
   p.disc(x,y,0.8+hash(j*5+2)*1.2,CORONA[5],k2*0.8);
  }
 }
 for(let j=0;j<4;j++){
  const side=j<2?-1:1,idx=j%2;
  const bx=side*(26+idx*28)+(hash(j*3+8)-0.5)*6;
  const sway=Math.sin(time*2.6+j*1.4)*5;
  const span=60+idx*18;
  const headY=-8-((time*0.72+hash(j*9+4))%1)*150;
  for(let y=headY;y<headY+span;y+=1){
   const u=(y-headY)/span;
   const lv=Math.min(7,Math.floor((1-u)*8*env));
   if(lv<=0)continue;
   const grow=Math.min(1,u*6);
   const x=bx+sway*(1-u*0.6)+Math.sin(y*0.1+time*6+j)*2.0*(1-u*0.4);
   p.disc(x,y,1.3*grow,lv>=6?CORONA[7]:CORONA[lv],0.5*env*(1-u*0.5));
  }
  p.disc(bx+sway*0.4,headY,2.2,CORONA[7],0.85*env);p.glow(bx+sway*0.4,headY,8,CORONA[6],0.22*env);
 }
 for(const by of [-52,-96,-138]){
  const spin=(time*0.95+hash(by)*0.3)%1;
  for(let k=0;k<7;k++){
   const q=((spin+k/7)%1),x=(q*2-1)*QRX*0.9;
   const edge=1-Math.abs(q*2-1)*0.35;
   p.disc(x,by+Math.sin(q*Math.PI*2+time*3)*3,1.2,CORONA[q<0.5?5:6],0.45*env*edge);
  }
 }
 const topGlow=0.55+0.45*Math.sin(time*5.0),topEnv=env*env;
 p.glow(0,QCCY-QRY-2,20+topGlow*8,CORONA[6],0.2*topEnv);
 p.disc(0,QCCY-QRY-2,2.0,CORONA[7],0.75*topEnv);
 for(let j=0;j<8;j++){
  const a=(time*0.8+hash(j*7+1)*1.4)%1,x=(hash(j*3+2)-0.5)*QRX*1.4*(1-a*0.6),y=-4-a*34,k=(1-a)*env;
  p.disc(x,y,1+hash(j)*1.0,CORONA[4],k*0.5);p.glow(x,y,4,CORONA[3],k*0.07);
 }
 const rgba=composite(frame,new Uint8ClampedArray(QW*QH*4),null);
 for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]<4)rgba.fill(0,i,i+4);
 return rgba;
}

const SPECS={
 'zero_strong_corona_fx_wide_beam':{n:4,W:420,H:96,AX:0,AY:48,loop:true,layer:'beam',pal:CORONA,draw:(p,ph)=>wideBeamBody(p,396,44,CORONA,ph)},
 'zero_strong_corona_fx_wide_hit':{n:4,W:128,H:128,AX:64,AY:64,layer:'impact',pal:CORONA,draw:(p,ph)=>hitBurst(p,50,CORONA,ph,0.36)},
 'zero_strong_corona_fx_emerium_beam':{n:4,W:420,H:72,AX:0,AY:36,loop:true,layer:'beam',pal:EMER,draw:(p,ph)=>emeriumBody(p,398,28,EMER,ph)},
 'zero_strong_corona_fx_emerium_hit':{n:4,W:120,H:120,AX:60,AY:60,layer:'impact',pal:EMER,draw:(p,ph)=>hitBurst(p,46,EMER,ph,0.36)},
 'zero_strong_corona_fx_slugger_flight':{n:4,W:64,H:48,AX:44,AY:24,loop:true,layer:'flight',pal:SLUG,draw:(p,ph)=>sluggerBlade(p,ph,SLUG)},
 'zero_strong_corona_fx_slugger_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,layer:'trail',pal:SLUG,draw:(p,ph)=>sluggerTrail(p,ph,SLUG)},
 'zero_strong_corona_fx_slugger_hit':{n:4,W:104,H:104,AX:52,AY:52,layer:'impact',pal:SLUG,draw:(p,ph)=>hitBurst(p,38,SLUG,ph,0.4)},
 'zero_strong_corona_fx_slugger_catch':{n:4,W:80,H:80,AX:40,AY:40,layer:'impact',pal:SLUG,draw:(p,ph)=>catchFlash(p,ph,SLUG)},
};
const exports=[];
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder,{recursive:true});
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];
 for(let i=0;i<spec.n;i++){
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  spec.draw(p,ph,i/spec.n,spec.W,spec.H,spec.AX,spec.AY);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  for(let j=0;j<rgba.length;j+=4){
   if(rgba[j+3]<4){rgba.fill(0,j,j+4);continue;}
   if(rgba[j+3]<128){rgba[j+3]=0;continue;}
   rgba[j+3]=255;
   if(spec.pal){
    let best=0,bestD=1e9;
    for(let k=0;k<spec.pal.length;k++){
     const c=spec.pal[k],r=(c&255),g=((c>>>8)&255),b=((c>>>16)&255);
     const dr=rgba[j]-r,dg=rgba[j+1]-g,db=rgba[j+2]-b,d=dr*dr+dg*dg+db*db;
     if(d<bestD){bestD=d;best=k;}
    }
    const c=spec.pal[best];rgba[j]=c&255;rgba[j+1]=(c>>>8)&255;rgba[j+2]=(c>>>16)&255;
   }
  }
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,kind:spec.layer,n:spec.n,W:spec.W,H:spec.H,AX:spec.AX,AY:spec.AY,loop:!!spec.loop,cols,rects,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
for(const [state,count] of [['q_charge_start',9],['q_charge',24],['q_charge_stop',9]]){
 const id=`zero_strong_corona_fx_${state}`,folder=join(OUT,id);mkdirSync(folder,{recursive:true});
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(QW*cols*QH*rows*4),rects=[],hashes=[];
 for(let i=0;i<count;i++){
  const env=state==='q_charge_start'?(i+1)/count:state==='q_charge_stop'?Math.max(0.08,(count-1-i)/(count-1)):1;
  const rgba=chargeAura(i+(state==='q_charge'?9:state==='q_charge_stop'?33:0),env),x=i%cols*QW,y=Math.floor(i/cols)*QH;
  for(let row=0;row<QH;row++)atlas.set(rgba.subarray(row*QW*4,(row+1)*QW*4),((y+row)*QW*cols+x)*4);
  const png=encodePNG(QW,QH,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,QW,QH]);
 }
 const png=encodePNG(QW*cols,QH*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,state,kind:'charge',n:count,W:QW,H:QH,AX:QAX,AY:QAY,loop:state==='q_charge',behind:true,cols,rects,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.zero-strong-corona-fx-family.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length}));
