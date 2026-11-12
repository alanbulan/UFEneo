// PixelFX离线烘焙：Q 蓄能周身气圈（盖亚青蓝：暗青→白热）。双侧沿椭圆环上升的实体流带、环顶汇聚光斑、
// 底部能量回流；不画椭圆硬线、不改人物与判定。照 black_king q-outline 管线模式。
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
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711102;
const SHA=b=>createHash('sha256').update(b).digest('hex');
// 盖亚青蓝：暗青→白热：暗蓝→白热
const PAL=fit(['#0a2e4d','#144a8f','#2a7fcf','#4dafe8','#7acef2','#a8e4f9','#d4f5ff','#ffffff'],8);
const NOISE=noiseFor(.4);
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
const TAU=Math.PI*2;
// 几何：佐菲头顶高154、身宽85（192格锚[96,184]→本画布锚=脚底中央）
// 环椭圆: 底部脚踝上方8px、顶过头顶约14px；环底留缺口不闭合
const W=384,H=256,AX=192,AY=246,CCY=-86,RX=84,RY=80;
function ringPoint(th,side){ // side -1/1: 环按透视压扁, 前后半各占 x*side
  const x=side*RX*Math.max(0.18,Math.abs(Math.sin(th)));
  const y=CCY+RY*Math.cos(th);
  return [AX+x*0+side*x, AY+y];
}
function paint(t,env){
 const frame=createFrame(W,H),p=painterFor(frame).place(AX,AY);
 p.lightK=.55;
 const time=t/60;
 // 双侧主气旋：三股沿环上升的流带，每股只占环的 55% 弧长、头部亮白粗、尾部暗蓝细并渐隐；
 // 环底留缺口（参数角 0.08π..0.92π），不是闭合椭圆线
 for(let side=-1;side<=1;side+=2){
  for(let k=0;k<3;k++){
   const speed=0.30+k*0.09, phase=((time*speed+k*0.31+hash(side*7+k*13+1)*0.1)%1);
   const len=0.55, GAP=0.08;             // 流带弧长、底部缺口
   for(let u=0;u<len;u+=0.004){
    const a=((phase+u)%1)*Math.PI*(1-2*GAP)+GAP*Math.PI;  // 0.08π..0.92π 底→顶
    const x=side*RX*Math.max(0.12,Math.sin(a))*(1+0.05*Math.sin(time*4+k));
    const y=CCY+RY*Math.cos(a);
    const head=1-u/len;                    // 1=头部亮
    const tail=u/len;
    // charge_start 时底部先亮：越靠环顶渐入越晚
    const envY=env*(0.45+0.55*(1-a/Math.PI));
    const lv=Math.min(7,Math.floor(head*head*9*envY));
    if(lv<=0)continue;
    const wob=Math.sin(time*9+k*2.4+u*20)*2.6;
    const size=(0.6+head*2.6)*envY;         // 头粗尾细
    p.disc(x+wob,y,size,PAL[lv],Math.min(1,(0.85-tail*0.55)*envY+0.15));
    if(lv>=6){p.disc(x+wob,y,size*0.5,PAL[7],0.9*envY);p.glow(x+wob,y,7+head*9,PAL[5],0.15*envY);}
   }
  }
  // 环侧碎光点：小粒子沿环散落上升
  for(let j=0;j<7;j++){
   const spd=0.22+hash(side*31+j*7+3)*0.2, ph=((time*spd+j*0.14+side*0.4)%1);
   const thUse=ph*Math.PI;
   const x=side*RX*Math.max(0.15,Math.sin(thUse))*0.92+(hash(j+side*11+9)-0.5)*10;
   const y=CCY+RY*Math.cos(thUse);
   const k2=(0.4+0.6*Math.sin(ph*Math.PI))*env;
   p.disc(x,y,0.8+hash(j*5+2)*1.3,PAL[5],k2*0.85);
  }
 }
 // 环顶汇聚光斑：单点，微呼吸
 const topGlow=0.55+0.45*Math.sin(time*5.2);
 const topEnv=env*env;                    // 渐入最后才亮顶
 p.glow(0,CCY-RY-2,22+topGlow*8,PAL[6],0.22*topEnv);
 p.disc(0,CCY-RY-2,2.2,PAL[7],0.8*topEnv);
 // 底部能量回流：脚踝高度向内汇聚的小流
 for(let j=0;j<8;j++){
  const a=(time*0.85+hash(j*7+1)*1.4)%1,x=(hash(j*3+2)-0.5)*RX*1.5*(1-a*0.6),y=-4-a*34;
  const k=(1-a)*env;
  p.disc(x,y,1+hash(j)*1.1,PAL[4],k*0.55);p.glow(x,y,4,PAL[3],k*0.08);
 }
 const rgba=composite(frame,new Uint8ClampedArray(W*H*4),null);
 for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]<4)rgba.fill(0,i,i+4);
 return rgba;
}
const exports=[],bindings={};
for(const [state,count] of [['charge_start',9],['charge',24],['charge_stop',9]]){
 const id=`ultraman_gaia_fx_q_${state}`,folder=join(OUT,id);mkdirSync(folder);
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(W*cols*H*rows*4),rects=[],hashes=[];
 for(let i=0;i<count;i++){
  const env=state==='charge_start'?(i+1)/count:state==='charge_stop'?Math.max(0,(count-1-i)/(count-1)):1;
  const rgba=paint(i+(state==='charge'?9:state==='charge_stop'?33:0),env),x=i%cols*W,y=Math.floor(i/cols)*H;
  for(let row=0;row<H;row++)atlas.set(rgba.subarray(row*W*4,(row+1)*W*4),((y+row)*W*cols+x)*4);
  const png=encodePNG(W,H,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,W,H]);
 }
 const png=encodePNG(W*cols,H*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 bindings[state]={id,texture:`res://assets/effects/ultraman-gaia/q-outline-pixelfx-20261111-v1/${id}/atlas.png`,rects,anchor:[AX,AY],ticks:1,display_scale:[1,1],behind_fighter:true,full_frame:true,source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',authoring_source:'res://tools/rebuild/ultraman-gaia/q-outline-pixelfx-20261111-v1/bake.mjs'};
 exports.push({state,count,W,H,AX,AY,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'provenance.json'),JSON.stringify({schema:'ufeneo.pixelfx.ultraman-gaia-q-outline.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:Object.keys(bindings)}));
