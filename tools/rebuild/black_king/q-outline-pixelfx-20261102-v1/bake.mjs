// PixelFX离线烘焙：躯干两侧分层火舌、撕落火团和火星。按用户纠正排除尾巴；不画椭圆线。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {noiseFor,flameTongue,looped,ember,firePuff,BIG_LAYERS,BACK_LAYERS} from '../../../../third_party/pixelfx/src/fx/fire/_lib.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const ART=join(ROOT,'art/fighters/black_king/stage4/q-outline-pixelfx-20261102-v1');
const opt=process.argv.indexOf('--out');if(opt<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[opt+1]);if(existsSync(OUT))throw Error('拒绝覆盖');mkdirSync(OUT,{recursive:true});
const shape=JSON.parse(readFileSync(join(ART,'shape-v7.json'),'utf8')),[w,h]=shape.size;
const SHA=b=>createHash('sha256').update(b).digest('hex');
const palette=fit(['#411317','#7e1f19','#bb3620','#ed6026','#ff963c','#ffc85c','#ffe58d','#fff3c4','#ffffff'],9);
const HOT=[...palette].reverse(),NOISE=noiseFor(.4);
function hash(n){n=Math.imul((n^711102)^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function paint(t,env){
 const frame=createFrame(w,h),p=painterFor(frame).place(...shape.anchor),time=t/60;
 p.fade=env;p.lightK=.7;
 const N=(rate,seed=0,off=0)=>NOISE(time,rate,seed,off);
 // 两排不对称火舌：主色块有体积，暗红后层、橙黄中层、白热细芯；中间留给完整人物。
 const sites=shape.sites;
 for(let i=0;i<sites.length;i++){
  const [x,y,h,wide,back]=sites[i],s=791+i*31,amplitude=.82+.2*N(9,s),sway=N(13,s+2)*15;
  flameTongue(p,x+N(12,s+3)*4,y,h*amplitude,wide*(.86+.2*N(14,s+4)),sway,N,s,HOT,back?BACK_LAYERS:BIG_LAYERS,1.7,6);
  p.glow(x,y-h*.35,21,palette[4],.16);
 }
 // 脱离的大块火屑各自冷却、翻卷；没有沿椭圆均匀排列的短线。
 looped(time,.4,102,791102,r=>({side:r.chance(.5)?-1:1,u:r.range(0,1),life:r.range(.16,.3),size:r.range(3,7),j:r.range(-8,8)}),(q,age)=>{
  const k=1-age/q.life,baseY=-8-q.u*187,x=q.side<0?-24+q.u*90:121-q.u*4;
  const xx=x+q.j+Math.sin(age*18+q.u*9)*7*q.side,yy=baseY-age*65;
  firePuff(p,xx,yy,k,q.size,q.u,HOT,.14,q.side*.7,-.7);
 });
 looped(time,.4,54,791803,r=>({side:r.chance(.5)?-1:1,y:r.range(-8,-205),life:r.range(.15,.33),j:r.range(-10,10),size:r.chance(.1)?2:1}),(q,age)=>{
  const k=1-age/q.life,x=(q.side<0?-34+(Math.abs(q.y)/210)*91:137)+q.j+q.side*age*12;
  ember(p,x,q.y-age*61,k,q.size,[HOT[1],HOT[2],HOT[4],HOT[7]],age*24);
 });
 // 脚边是零散热流，没有地面圆圈或整人发亮底板。
 for(let j=0;j<8;j++){
  const x=-26+j*22,life=(t/24+hash(j+31))%1;
  if(j%3!==1)firePuff(p,x,-life*10,1-life,2+hash(j+13)*1.8,life,HOT,.1);
 }
 const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);
 for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]<4)rgba.fill(0,i,i+4);
 return rgba;
}
const exports=[],bindings={};
for(const [state,count] of [['charge_start',9],['charge',24],['charge_stop',9]]){
 const id='black_king_q_outline_'+state,folder=join(OUT,id);mkdirSync(folder);
 const cols=6,rows=Math.ceil(count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4),rects=[],hashes=[];
 for(let i=0;i<count;i++){
  const env=state==='charge_start'?(i+1)/count:state==='charge_stop'?(count-1-i)/(count-1):1;
  const rgba=paint(i+(state==='charge'?9:state==='charge_stop'?33:0),env),x=i%cols*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,w,h]);
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 const clip={texture:`res://assets/effects/black_king/q-outline-pixelfx-20261102-v1/${id}/atlas.png`,rects,anchor:shape.anchor,ticks:1,display_scale:[1,1],behind_fighter:true,full_frame:true,
 source_kind:'pixelfx_code_baked',upstream_commit:'a84159688af3ca37a4be05a0d422b94451b2e24e',license:'MIT',authoring_source:'res://tools/rebuild/black_king/q-outline-pixelfx-20261102-v1/bake.mjs'};
 bindings[state]={effect:id,anchor:[0,0],color:[1,1,1,1],behind_fighter:true,clip};
 exports.push({id,state,count,atlas_sha256:SHA(png),phase_png_sha256:hashes});
}
writeFileSync(join(OUT,'bindings.json'),JSON.stringify(bindings,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.black-king.Q-body-fire.pixelfx.v7',upstream:'https://github.com/patch-gg/pixelfx',upstream_commit:'a84159688af3ca37a4be05a0d422b94451b2e24e',license:'MIT',authoring_sha256:SHA(readFileSync(SELF)),shape_sha256:SHA(readFileSync(join(ART,'shape-v7.json'))),fire_helper_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/src/fx/fire/_lib.js'))),license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),excludes_tail:true,continuous_ellipse_outline:false,exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,exports:exports.map(v=>({id:v.id,count:v.count}))}));
