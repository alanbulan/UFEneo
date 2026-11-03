// 布莱克王口部热束：热核、翻卷火舌和独立火屑；离线整相，不改人物或判定。
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要--out新目录');
const OUT=resolve(ROOT,process.argv[at+1]);if(!OUT.startsWith(ROOT+'\\')&&!OUT.startsWith(ROOT+'/'))throw Error('输出必须在工程内');
if(existsSync(join(OUT,'bundle.json')))throw Error('拒绝覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e',SEED=711102;
const SHA=b=>createHash('sha256').update(b).digest('hex');
const PAL=fit(['#371225','#6b1925','#a42a25','#df4825','#ff792f','#ffa949','#ffd778','#fff1b5','#fff9e5','#ffffff'],10);
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function ease(v){return v*v*(3-2*v);}
function noise(x,y,salt){let a=Math.floor(x),b=Math.floor(y),u=ease(x-a),v=ease(y-b);return (hash(a+b*1301+salt)*(1-u)+hash(a+1+b*1301+salt)*u)*(1-v)+(hash(a+(b+1)*1301+salt)*(1-u)+hash(a+1+(b+1)*1301+salt)*u)*v;}
function heat(p,t,s){
 const fade=t<s.count-4?1:[.85,.6,.35,.12][t-s.count+4],env=(t===0?.68:t===1?.9:1)*fade;
 for(let x=0;x<s.length;x++){
  const flow=x-t*23,bulge=noise(flow/32,0,197),bend=(noise(flow/59,0,503)-.5)*s.radius*.4;
  const root=Math.min(1,(x+4)/24),tip=Math.min(1,(s.length-x)/40),r=s.radius*(.72+bulge*.57)*root*tip;
  for(let y=-Math.ceil(s.radius*1.9);y<=Math.ceil(s.radius*1.9);y++){
   const curl=noise(flow/17,(y+t*.9)/7,941),q=Math.abs(y-bend)/Math.max(.3,r),density=1.32-q+curl*.42;
   if(density<.17||q>1.7)continue;
   const coarse=noise(flow/43,(y+t*.3)/11,2311),heat=Math.max(0,Math.min(1,(1-q*.7)*.79+curl*.27+coarse*.16));
   const index=Math.min(9,Math.max(0,Math.floor(heat*9)));
   const alpha=Math.min(1,(density-.17)*1.7)*(q<.8?1:.76)*env;
   p.blend(x,y,PAL[index],alpha);
  }
  if(x%7===0)p.glow(x,bend,r*1.3+3,PAL[4],.10*env*tip);
 }
 // 弯曲火舌及短寿火屑各自运动；每相直接画完整跨度，不重复短片。
 for(let j=0;j<82;j++){
  const a=(t+hash(j+4001)*7)%7,x=8+hash(j+5003)*(s.length-50)+a*4;if(x>s.length-6)continue;
  const sign=hash(j+6007)>.5?1:-1,y=sign*(s.radius*(.75+hash(j+7001)*.35)+a*.8),k=(1-a/7)*env;
  const tail=5+hash(j+8009)*22;
  p.polyline([[x-tail,y*.65],[x-tail*.4,y+sign*2],[x,y]],PAL[5],k*.8);
  p.disc(x,y,.7+hash(j+9001),PAL[7],k);p.glow(x,y,3,PAL[4],k*.18);
 }
 p.glow(1,0,6+s.radius*.3,PAL[6],env*.3);p.disc(1,0,1.4,PAL[9],env);
}
const specs=[{level:2,length:480,count:8,size:[528,104],anchor:[24,52],radius:14},
 {level:1,length:640,count:16,size:[688,88],anchor:[24,44],radius:8},
 {level:2,length:640,count:16,size:[688,136],anchor:[24,68],radius:19},
 {level:3,length:640,count:16,size:[688,192],anchor:[24,96],radius:30}];
const bindings={},exports=[];
for(const spec of specs){
 const id=`black_king_heat_pixelfx_${spec.length}_${spec.level}`,folder=join(OUT,id);mkdirSync(folder);
 const [w,h]=spec.size,cols=4,rows=Math.ceil(spec.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4),rects=[],frames=[],hashes=[];
 for(let i=0;i<spec.count;i++){
  const frame=createFrame(w,h),p=painterFor(frame).place(...spec.anchor);heat(p,i,spec);
  const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);for(let j=0;j<rgba.length;j+=4)if(rgba[j+3]<3)rgba.fill(0,j,j+4);
  const x=i%cols*w,y=Math.floor(i/cols)*h;for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba);writeFileSync(join(folder,String(i).padStart(2,'0')+'.png'),png);hashes.push(SHA(png));rects.push([x,y,w,h]);
  frames.push({filename:String(i).padStart(2,'0')+'.png',frame:{x,y,w,h},rotated:false,trimmed:false,spriteSourceSize:{x:0,y:0,w,h},sourceSize:{w,h},duration:1000/60});
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 writeFileSync(join(folder,'aseprite.json'),JSON.stringify({frames,meta:{app:'https://github.com/patch-gg/pixelfx',image:'atlas.png',format:'RGBA8888',size:{w:w*cols,h:h*rows},scale:'1',pixelfx:{fps:60,pivot:spec.anchor,frameSize:spec.size,loop:false}}},null,2)+'\n');
 bindings[spec.length+':'+spec.level]={id,texture:`res://assets/effects/black_king/heatbeam-pixelfx-20261102-v1/${id}/atlas.png`,rects,anchor:spec.anchor,ticks:1,loop:false,display_scale:[1,1],visual_scale:1,full_frame:true,emission_anchor:true,source_kind:'pixelfx_code_baked',upstream_commit:UPSTREAM,license:'MIT',authoring_source:'res://tools/rebuild/black_king/heatbeam-pixelfx-20261102-v1/bake.mjs'};
 exports.push({...spec,id,phase_png_sha256:hashes,atlas_sha256:SHA(png)});
}
writeFileSync(join(OUT,'bindings.json'),JSON.stringify(bindings,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.black-king-heat.v1',source_kind:'pixelfx_code_baked',route:'offline',upstream_commit:UPSTREAM,upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,seed:SEED,license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),source_sha256:SHA(readFileSync(SELF)),exports},null,2)+'\n');
console.log(JSON.stringify({out:OUT,effects:exports.map(s=>s.id)}));
