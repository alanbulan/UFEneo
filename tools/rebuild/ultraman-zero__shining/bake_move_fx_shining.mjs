// 光辉赛罗专属招式特效（8 段）：金白主体、蓝白亮芯、放射光晕与金色星屑。
// 尺寸/帧数/锚点/循环与基础赛罗对应段一致；形状独立烘焙，非复制基础图集。
import {createFrame,painterFor,composite} from '../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[at+1]);if(existsSync(join(OUT,'provenance.json')))throw Error('拒绝覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=2026111201;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
const TAU=Math.PI*2;
const GOLD=fit(['#1a1206','#3d2a08','#745212','#b07a10','#d8a818','#f4d458','#fff6b8','#ffffff'],8);
const CORE=fit(['#061628','#0c3050','#1a5880','#2f88b8','#70c8e8','#b8ecff','#eefcff','#ffffff'],8); // 蓝白亮芯
const SLUGGER=fit(['#161208','#403414','#7a6020','#b89828','#e0c850','#fff0a0','#ffffff','#d8f4ff'],8);
const EMERIUM=fit(['#1a1408','#4a3610','#8a6420','#c89418','#f0c838','#fff4a8','#ffffff','#d0f0ff'],8);

function goldDust(p,cx,cy,R,count,ph,spread=1){
 for(let j=0;j<count;j++){
  const a=hash(j*17+13)*TAU,sp=R*0.4+hash(j*23+7)*R*spread;
  const tw=(((ph*1.3+hash(j*29+3))%1)+1)%1;
  const d=tw*sp,x=cx+Math.cos(a)*d,y=cy+Math.sin(a)*d-Math.sin(tw*Math.PI)*R*0.12;
  const k=1-tw; if(k<0.12)continue;
  const c=k>0.7?GOLD[7]:k>0.45?GOLD[6]:GOLD[5];
  p.disc(x,y,k>0.55?1.4:0.8,c,k*0.9);
  if((j&3)===0&&k>0.5){p.dot(x+1,y,c,0.7);p.dot(x-1,y,c,0.7);p.dot(x,y+1,c,0.7);p.dot(x,y-1,c,0.7);}
 }
}
function star(p,cx,cy,r,ph,spikes=4){
 const base=ph*TAU*0.25;
 for(let k=0;k<spikes;k++){
  const a=base+k*TAU/spikes;
  const len=r*(0.75+0.25*Math.sin(ph*TAU*3+k*1.7));
  p.line(cx,cy,cx+Math.cos(a)*len,cy+Math.sin(a)*len,(u)=>(u<0.45?CORE[7]:CORE[5]));
  const a2=a+TAU/(spikes*2);
  p.line(cx,cy,cx+Math.cos(a2)*len*0.55,cy+Math.sin(a2)*len*0.55,(u)=>(u<0.5?GOLD[7]:GOLD[5]),0.75);
 }
 p.circle(cx,cy,r*0.22,CORE[6]);p.circle(cx,cy,r*0.12,CORE[7]);
}
function radiantHalo(p,cx,cy,r,ph,str=1){
 for(let k=0;k<2;k++){
  const q=(((ph*1.6+k/2)%1)+1)%1;
  p.ring(cx,cy,r*0.3+r*0.9*q,Math.max(1,2.2*(1-q)),q<0.35?GOLD[7]:GOLD[5],(1-q)*0.75*str);
 }
 p.glow(cx,cy,r*0.7,GOLD[5],0.25*str);
}
function wideBeamBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const w=thick*0.5*(1+0.06*Math.sin(d*0.21-ph*TAU*5))*Math.min(1,(d+4)/10)*Math.min(1,(len-d)/18+0.28);
  const notch=((d*0.42-ph*len*0.5)%17+17)%17<5;
  for(let q0=-w*1.28;q0<=w*1.28;q0+=0.5){
   const qn=Math.abs(q0)/w;
   if(notch&&qn>0.9)continue;
   let c;
   if(qn<0.10)c=CORE[7]; else if(qn<0.24)c=CORE[6]; else if(qn<0.42)c=PAL[7];
   else if(qn<0.62)c=PAL[6]; else if(qn<0.8)c=PAL[5]; else if(qn<0.94)c=PAL[4]; else c=PAL[3];
   p.px(d,q0,c);
  }
  for(const s of [-1,1]){
   const a=d*0.15-ph*TAU*3+s*Math.PI*0.5;
   const off=Math.sin(a)*w*1.16;
   if(Math.cos(a)>0.15)p.dot(d,off,Math.cos(a)>0.6?GOLD[7]:GOLD[5],0.85);
  }
  if(Math.round(d*2)%144===0){
   const l=(thick*0.5)*(1.1+0.5*Math.sin(ph*TAU*4+d*0.03));
   p.line(d,0,d,-l,GOLD[6],0.9);p.line(d,0,d,l,GOLD[6],0.9);
   p.dot(d,-l,CORE[7]);p.dot(d,l,CORE[7]);
  }
  if((Math.round(d*2)&15)===0)p.glow(d,0,w*2.2+3,GOLD[5],0.1);
  if((Math.round(d*3)&7)===0){
   const sy=(hash(Math.floor(d)*7+Math.floor(ph*20))*2-1)*w*1.55;
   p.disc(d,sy,0.9,(hash(Math.floor(d)*11)&1)?GOLD[7]:GOLD[6],0.85);
  }
 }
 star(p,3,0,thick*0.52,ph,4); radiantHalo(p,3,0,thick*0.55,ph,1.1);
 p.circle(0,0,thick*0.2,CORE[6]);p.circle(0,0,thick*0.1,CORE[7]); p.glow(0,0,thick*0.9,GOLD[5],0.65);
 const tip=thick*0.55;
 p.line(len,0,len+tip,0,CORE[7]);p.line(len,-tip*0.7,len,0,GOLD[6]);p.line(len,tip*0.7,len,0,GOLD[6]);
 radiantHalo(p,len,0,thick*0.5,ph,1.0);
 p.circle(len,0,tip*0.55,PAL[5]);p.circle(len,0,tip*0.3,CORE[7]); p.glow(len,0,thick*0.9,GOLD[5],0.7);
 goldDust(p,len*0.55,0,thick*1.4,10,ph,1.1);
}
function emeriumBody(p,len,thick,PAL,ph){
 for(let d=0;d<=len;d+=0.5){
  const w=thick*0.5*(1+0.05*Math.sin(d*0.3-ph*TAU*6))*Math.min(1,(d+3)/8)*Math.min(1,(len-d)/16+0.3);
  for(let q0=-w*1.15;q0<=w*1.15;q0+=0.5){
   const qn=Math.abs(q0)/w;
   let c;
   if(qn<0.18)c=CORE[7]; else if(qn<0.36)c=CORE[6]; else if(qn<0.56)c=PAL[7];
   else if(qn<0.76)c=PAL[6]; else if(qn<0.92)c=PAL[5]; else c=PAL[4];
   p.px(d,q0,c);
  }
  for(const s of [-1,1]){const off=Math.sin(d*0.24-ph*TAU*4+s)*w*1.05;if(Math.sin(d*0.24-ph*TAU*4+s)>0.2)p.dot(d,off,GOLD[7],0.8);}
  if((Math.round(d*4)&9)===0){const sy=(hash(Math.floor(d)*5+1)*2-1)*w*1.3;p.disc(d,sy,0.8,GOLD[6],0.8);}
 }
 for(let k=0;k<4;k++){
  const cx=((k+ph)%4)*(len/4)+10;
  for(let a=-1.15;a<=1.15;a+=0.055){
   const r=thick*0.95+2.5*Math.sin(a*2.2+ph*TAU);
   const x=cx+Math.cos(a)*r*0.55,y=Math.sin(a)*r;
   p.disc(x,y,1.5,Math.abs(a)<0.5?CORE[7]:GOLD[6],0.85);
  }
 }
 star(p,3,0,thick*0.5,ph,4); radiantHalo(p,3,0,thick*0.5,ph,1.0);
 p.circle(0,0,thick*0.18,CORE[6]);p.circle(0,0,thick*0.09,CORE[7]); p.glow(0,0,thick*0.85,GOLD[5],0.6);
 for(let a=-1.5;a<=1.5;a+=0.05){ const r=thick*1.5; p.disc(len+Math.cos(a)*r*0.7,Math.sin(a)*r,1.4,Math.abs(a)<0.4?CORE[7]:GOLD[6],0.9); }
 radiantHalo(p,len,0,thick*0.65,ph,1.0); p.glow(len,0,thick*1.1,GOLD[5],0.65);
 goldDust(p,len*0.5,0,thick*1.2,9,ph,1.0);
}
function sluggerBlade(p,ph,PAL){
 const ang=ph*TAU*0.5-0.35; const ca=Math.cos(ang),sa=Math.sin(ang);
 const put=(x,y,c,a=1)=>p.disc(x*ca-y*sa,y*ca+x*sa,1.4,c,a);
 for(let a=-1.35;a<=1.35;a+=0.035){
  for(let r=8;r<=14;r+=0.6){
   const u=(r-8)/6; let c;
   if(Math.abs(a)>1.1)c=CORE[7]; else if(u>0.62)c=PAL[7]; else if(u>0.3)c=PAL[5]; else c=PAL[4];
   put(Math.cos(a)*r-2,Math.sin(a)*r,c,0.95);
  }
 }
 for(let a=-1.2;a<=1.2;a+=0.04)put(Math.cos(a)*14,Math.sin(a)*14,CORE[7],0.95);
 for(let a=-1.05;a<=1.05;a+=0.05)put(Math.cos(a)*9.4-2,Math.sin(a)*9.4,PAL[3],0.9);
 for(let k=0;k<2;k++){ const a0=ph*TAU*1.5+k*Math.PI; for(let u=0;u<0.4;u+=0.04){const a=a0+u;put(Math.cos(a)*12.2,Math.sin(a)*12.2,u<0.18?CORE[7]:GOLD[6],1-u*1.6);} }
 put(0,0,2.2,CORE[7]);p.glow(0,0,10,GOLD[5],0.35); goldDust(p,0,0,12,6,ph,0.8);
}
function sluggerTrail(p,ph,PAL){
 for(let d=0;d<132;d+=1){
  const u=d/132,x=-d,y=Math.sin(d*0.26-ph*TAU*2.4)*4.2*u;
  if(((d+Math.floor(ph*9))%3)<2){
   const c=u<0.2?CORE[7]:u<0.45?GOLD[7]:u<0.7?GOLD[6]:GOLD[5];
   p.px(x,y,c); if(u<0.6)p.px(x,y+1,GOLD[Math.max(3,6-Math.floor(u*4))]);
  }
  if(d%7===0)p.dot(x,y,GOLD[7],0.65*(1-u));
  if(d%13===0)p.glow(x,y,3,GOLD[5],0.1*(1-u));
  if(d%11===0)p.disc(x,y+(hash(d*3)&1?2:-2),0.8,GOLD[6],0.5*(1-u));
 }
 p.circle(0,0,2.6,CORE[6]);p.circle(0,0,1.4,CORE[7]);p.glow(0,0,12,GOLD[5],0.3); goldDust(p,-40,0,18,8,ph,1.2);
}
function hitBurst(p,R,PAL,ph,dur){
 const grow=Math.min(1,(ph*dur)/0.12),k=1-ph,R0=R*0.42*grow;
 for(let i=0;i<8;i++){ const a=i*TAU/8+ph*2.4,l=R0*(1.4+0.75*Math.sin(ph*TAU*5+i*1.7)); p.line(0,0,Math.cos(a)*l,Math.sin(a)*l,(u)=>(u<0.45?CORE[7]:i%2?GOLD[7]:GOLD[6]),(u)=>(u<0.5?1:1.5-u)); }
 star(p,0,0,R0*0.9,ph,4); radiantHalo(p,0,0,R0*1.3,ph,1.1*k);
 p.circle(0,0,R0*0.5,CORE[7],k); p.glow(0,0,R*0.8,GOLD[5],0.65*k);
 for(let j=0;j<14;j++){ const a=hash(j*3+1)*TAU,sp=26+hash(j*7+2)*60,d0=ph*sp; const x=Math.cos(a)*d0,y=Math.sin(a)*d0-d0*d0*0.06,kk=1-ph; if(kk>0.12)p.disc(x,y,0.8+hash(j)*1.3,j%3?GOLD[7]:GOLD[6],kk*0.85); }
}
function catchFlash(p,ph,PAL){
 const k=1-ph;
 for(let i=0;i<3;i++){ const q=(((ph*1.4+i/3)%1)+1)%1; p.ring(0,0,26*(1-q)+3,Math.max(1,2.2*(1-q)),q<0.35?CORE[7]:GOLD[6],(1-q)*k*0.9); }
 radiantHalo(p,0,0,18,ph,0.9*k);
 for(let s=-1;s<=1;s+=2){ for(let u=0;u<1;u+=0.04){ const x=s*(4+u*9),y=-u*18+4; p.disc(x,y,u<0.2?CORE[7]:GOLD[6],(1-u*0.5)*k*0.9); } }
 star(p,0,0,10*(0.6+0.4*k),ph,4);
 p.circle(0,0,3.2,CORE[7],k);p.glow(0,0,22,GOLD[5],0.45*k); goldDust(p,0,0,22,10,ph,0.8);
}

const SPECS={
 'zero_shining_fx_wide_beam':{n:4,W:420,H:96,AX:0,AY:48,loop:true,layer:'beam',pal:GOLD,draw:(p,ph)=>wideBeamBody(p,396,44,GOLD,ph),color_parameter:true},
 'zero_shining_fx_wide_hit':{n:4,W:128,H:128,AX:64,AY:64,loop:false,layer:'impact',pal:GOLD,draw:(p,ph)=>hitBurst(p,50,GOLD,ph,0.36)},
 'zero_shining_fx_emerium_beam':{n:4,W:420,H:72,AX:0,AY:36,loop:true,layer:'beam',pal:EMERIUM,draw:(p,ph)=>emeriumBody(p,398,28,EMERIUM,ph),color_parameter:true},
 'zero_shining_fx_emerium_hit':{n:4,W:120,H:120,AX:60,AY:60,loop:false,layer:'impact',pal:EMERIUM,draw:(p,ph)=>hitBurst(p,46,EMERIUM,ph,0.36)},
 'zero_shining_fx_slugger_flight':{n:4,W:64,H:48,AX:44,AY:24,loop:true,layer:'flight',pal:SLUGGER,draw:(p,ph)=>sluggerBlade(p,ph,SLUGGER)},
 'zero_shining_fx_slugger_trail':{n:4,W:160,H:48,AX:128,AY:24,loop:true,layer:'trail',pal:SLUGGER,draw:(p,ph)=>sluggerTrail(p,ph,SLUGGER)},
 'zero_shining_fx_slugger_hit':{n:4,W:104,H:104,AX:52,AY:52,loop:false,layer:'impact',pal:SLUGGER,draw:(p,ph)=>hitBurst(p,38,SLUGGER,ph,0.4)},
 'zero_shining_fx_slugger_catch':{n:4,W:80,H:80,AX:40,AY:40,loop:false,layer:'impact',pal:SLUGGER,draw:(p,ph)=>catchFlash(p,ph,SLUGGER)},
};
const exports=[];
for(const [id,spec] of Object.entries(SPECS)){
 const folder=join(OUT,id);mkdirSync(folder);
 const cols=Math.min(4,spec.n),rows=Math.ceil(spec.n/cols);
 const atlas=new Uint8ClampedArray(spec.W*cols*spec.H*rows*4),rects=[],hashes=[];
 for(let i=0;i<spec.n;i++){
  const ph=spec.loop?(i/spec.n):(i/(spec.n-1||1));
  const frame=createFrame(spec.W,spec.H),p=painterFor(frame).place(spec.AX,spec.AY);
  spec.draw(p,ph,i/spec.n,spec.W,spec.H,spec.AX,spec.AY);
  const rgba=composite(frame,new Uint8ClampedArray(spec.W*spec.H*4),null);
  const pool=[...spec.pal,...CORE.slice(4),GOLD[6],GOLD[7]];
  const uniq=[]; const seen=new Set();
  for(const c of pool){if(!seen.has(c)){seen.add(c);uniq.push(c);}}
  for(let j=0;j<rgba.length;j+=4){
   if(rgba[j+3]<4){rgba.fill(0,j,j+4);continue;}
   if(rgba[j+3]<128){rgba[j+3]=0;continue;}
   rgba[j+3]=255;
   let best=0,bestD=1e9;
   for(let k=0;k<uniq.length;k++){
    const c=uniq[k],r=(c&255),g=((c>>>8)&255),b=((c>>>16)&255);
    const dr=rgba[j]-r,dg=rgba[j+1]-g,db=rgba[j+2]-b,d=dr*dr+dg*dg+db*db;
    if(d<bestD){bestD=d;best=k;}
   }
   const c=uniq[best];rgba[j]=c&255;rgba[j+1]=(c>>>8)&255;rgba[j+2]=(c>>>16)&255;
  }
  const x=(i%cols)*spec.W,y=Math.floor(i/cols)*spec.H;
  for(let row=0;row<spec.H;row++)atlas.set(rgba.subarray(row*spec.W*4,(row+1)*spec.W*4),((y+row)*spec.W*cols+x)*4);
  const png=encodePNG(spec.W,spec.H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,spec.W,spec.H]);
 }
 const png=encodePNG(spec.W*cols,spec.H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,kind:spec.layer,n:spec.n,W:spec.W,H:spec.H,AX:spec.AX,AY:spec.AY,loop:!!spec.loop,cols,rects,color_parameter:!!spec.color_parameter,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.shining-move-fx.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),identity:'gold-white body, blue-white core, radiant halo, golden stardust',exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length}));
