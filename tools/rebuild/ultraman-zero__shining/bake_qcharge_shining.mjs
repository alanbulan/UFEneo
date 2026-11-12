// 光辉赛罗 Q 蓄气三态：沿用 chargeAura 形状，蓝白亮芯 + 金白外辉/星屑，硬 Alpha。
// 形状来源：tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs chargeAura
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
const ci=process.argv.indexOf('--cutoff');
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=2026111202,CUTOFF=ci>=0?Number(process.argv[ci+1]):32;
const SHA=b=>createHash('sha256').update(b).digest('hex');
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
const CYAN=fit(['#03121f','#082a44','#0e4c74','#1a7fb8','#42b6e8','#8fdcf8','#d0f2ff','#ffffff'],8);
const GOLD=fit(['#1a1206','#3d2a08','#745212','#b07a10','#d8a818','#f4d458','#fff6b8','#ffffff'],8);
const TAU=Math.PI*2;

const QW=384,QH=256,QAX=192,QAY=246,QCCY=-96,QRX=78,QRY=92;
function chargeAura(t,env){
 const frame=createFrame(QW,QH),p=painterFor(frame).place(QAX,QAY);
 p.lightK=.55;
 const time=t/60;
 for(let side=-1;side<=1;side+=2){
  for(let k=0;k<3;k++){
   const speed=0.30+k*0.09,phase=((time*speed+k*0.31+hash(side*7+k*13+1)*0.1)%1),len=0.55,GAP=0.09;
   for(let u=0;u<len;u+=0.004){
    const a=((phase+u)%1)*Math.PI*(1-2*GAP)+GAP*Math.PI;
    const x=side*QRX*Math.max(0.12,Math.sin(a))*(1+0.05*Math.sin(time*4+k));
    const y=QCCY+QRY*Math.cos(a);
    const head=1-u/len,tail=u/len;
    const envY=env*(0.45+0.55*(1-a/Math.PI));
    const lv=Math.min(7,Math.floor(head*head*9*envY));
    if(lv<=0)continue;
    const wob=Math.sin(time*9+k*2.4+u*20)*2.6,size=(0.6+head*2.4)*envY;
    // 蓝白亮芯，外层带金色
    const c = lv>=6 ? (u<0.25?CYAN[7]:CYAN[6]) : (lv>=4 ? CYAN[lv] : GOLD[Math.max(3,lv+1)]);
    p.disc(x+wob,y,size,c,Math.min(1,(0.85-tail*0.55)*envY+0.15));
    if(lv>=6){p.disc(x+wob,y,size*0.5,CYAN[7],0.9*envY);p.glow(x+wob,y,7+head*9,GOLD[5],0.12*envY);}
   }
  }
  for(let j=0;j<7;j++){
   const spd=0.22+hash(side*31+j*7+3)*0.2,ph=((time*spd+j*0.14+side*0.4)%1),th=ph*Math.PI;
   const x=side*QRX*Math.max(0.15,Math.sin(th))*0.92+(hash(j+side*11+9)-0.5)*10;
   const y=QCCY+QRY*Math.cos(th),k2=(0.4+0.6*Math.sin(ph*Math.PI))*env;
   p.disc(x,y,0.8+hash(j*5+2)*1.3,j%2?GOLD[6]:CYAN[5],k2*0.85);
  }
 }
 // 头镖形刃光：金色掠刃 + 蓝白头亮
 for(let j=0;j<4;j++){
  const side=j<2?-1:1,idx=j%2;
  const bx=side*(26+idx*28)+(hash(j*3+8)-0.5)*6;
  const sway=Math.sin(time*2.4+j*1.3)*5;
  const span=58+idx*20;
  const headY=-8-((time*0.75+hash(j*9+4))%1)*150;
  for(let y=headY;y<headY+span;y+=1){
   const u=(y-headY)/span;
   const lv=Math.min(7,Math.floor((1-u)*8*env));
   if(lv<=0)continue;
   const grow=Math.min(1,u*6);
   const x=bx+sway*(1-u*0.6)+Math.sin(y*0.09+time*6+j)*2.2*(1-u*0.4);
   const c = u<0.18 ? CYAN[7] : (u<0.45 ? GOLD[7] : GOLD[Math.max(4,lv)]);
   p.disc(x,y,1.3*grow,c,0.55*env*(1-u*0.5));
  }
  p.disc(bx+sway*0.4,headY,2.4,CYAN[7],0.9*env);p.glow(bx+sway*0.4,headY,8,GOLD[6],0.25*env);
 }
 // 横向断弧：金色弧带
 for(const by of [-52,-96,-138]){
  const spin=(time*0.9+hash(by)*0.3)%1;
  for(let k=0;k<7;k++){
   const q=((spin+k/7)%1),x=(q*2-1)*QRX*0.92;
   const edge=1-Math.abs(q*2-1)*0.35;
   p.disc(x,by+Math.sin(q*Math.PI*2+time*3)*3,1.2,q<0.5?GOLD[6]:GOLD[5],0.5*env*edge);
  }
 }
 const topGlow=0.55+0.45*Math.sin(time*5.2),topEnv=env*env;
 p.glow(0,QCCY-QRY-2,22+topGlow*8,GOLD[6],0.2*topEnv);
 p.disc(0,QCCY-QRY-2,2.2,CYAN[7],0.8*topEnv);
 for(let j=0;j<8;j++){
  const a=(time*0.85+hash(j*7+1)*1.4)%1,x=(hash(j*3+2)-0.5)*QRX*1.5*(1-a*0.6),y=-4-a*34,k=(1-a)*env;
  p.disc(x,y,1+hash(j)*1.1,j%2?GOLD[5]:CYAN[4],k*0.55);p.glow(x,y,4,GOLD[4],k*0.08);
 }
 // 金色星屑点缀
 for(let j=0;j<10;j++){
  const ph=((time*0.6+hash(j*19+5))%1),a=hash(j*13+2)*TAU;
  const r=30+ph*70*env; const x=Math.cos(a)*r*0.7, y=QCCY-20-Math.sin(ph*Math.PI)*50+hash(j*5)*20;
  const k=(1-ph)*env*0.8; if(k>0.12) p.disc(x,y,0.9,j%2?GOLD[7]:GOLD[6],k);
 }
 p.disc(0,-5,1.6,CYAN[7],1); p.disc(0,-5,0.8,GOLD[7],1);
 return composite(frame,new Uint8ClampedArray(QW*QH*4),null);
}

function harden(rgba){
 for(let j=0;j<rgba.length;j+=4){
  if(rgba[j+3]<CUTOFF){rgba.fill(0,j,j+4);continue;}
  rgba[j+3]=255;
  let best=0,bestD=1e9;
  for(let k=0;k<CYAN.length;k++){
   const c=CYAN[k],r=(c&255),g=((c>>>8)&255),b=((c>>>16)&255);
   const dr=rgba[j]-r,dg=rgba[j+1]-g,db=rgba[j+2]-b,d=dr*dr+dg*dg+db*db;
   if(d<bestD){bestD=d;best=k;}
  }
  for(let k=0;k<GOLD.length;k++){
   const c=GOLD[k],r=(c&255),g=((c>>>8)&255),b=((c>>>16)&255);
   const dr=rgba[j]-r,dg=rgba[j+1]-g,db=rgba[j+2]-b,d=dr*dr+dg*dg+db*db;
   if(d<bestD){bestD=d;best=8+k;}
  }
  if(best<8){const c=CYAN[best];rgba[j]=c&255;rgba[j+1]=(c>>>8)&255;rgba[j+2]=(c>>>16)&255;}
  else {const c=GOLD[best-8];rgba[j]=c&255;rgba[j+1]=(c>>>8)&255;rgba[j+2]=(c>>>16)&255;}
 }
}

const exports=[];
for(const [state,count] of [['charge_start',9],['charge',24],['charge_stop',9]]){
 const id=`zero_shining_fx_q_${state}`,folder=join(OUT,id);mkdirSync(folder);
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(QW*cols*QH*rows*4),rects=[],hashes=[];
 for(let i=0;i<count;i++){
  const env=state==='charge_start'?(i+1)/count:state==='charge_stop'?Math.max(0.08,(count-1-i)/(count-1)):1;
  const rgba=chargeAura(i+(state==='charge'?9:state==='charge_stop'?33:0),env);
  harden(rgba);
  const x=i%cols*QW,y=Math.floor(i/cols)*QH;
  for(let row=0;row<QH;row++)atlas.set(rgba.subarray(row*QW*4,(row+1)*QW*4),((y+row)*QW*cols+x)*4);
  const png=encodePNG(QW,QH,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,QW,QH]);
 }
 const png=encodePNG(QW*cols,QH*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 exports.push({id,state,kind:'charge',n:count,W:QW,H:QH,AX:QAX,AY:QAY,loop:state==='charge',behind:true,cols,rects,
  phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({
 schema:'ufeneo.pixelfx.shining-qcharge.v1',source_kind:'pixelfx_code_baked',route:'offline',
 upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,
 license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),
 source_sha256:SHA(readFileSync(SELF)),
 shape_source:'tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs chargeAura',
 identity:'blue-white core with gold accents/radiance and golden stardust for Shining Ultraman Zero',
 hard_alpha_cutoff:CUTOFF,exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.length,cutoff:CUTOFF}));
