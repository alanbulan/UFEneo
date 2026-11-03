// 专用合掌短束：使用PixelFX MIT像素/光缓冲，全部在300原生跨度直接烘焙。
// 不载入actor/stock dummy，不生成或改动人物，不发网络请求。
import {createFrame,painterFor,composite,fit} from '../../../../third_party/pixelfx/src/core/index.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SELF=fileURLToPath(import.meta.url),ROOT=resolve(dirname(SELF),'../../../..');
const at=process.argv.indexOf('--out');
if(at<0)throw Error('需要 --out 新目录');
const OUT=resolve(ROOT,process.argv[at+1]);
if(!OUT.startsWith(ROOT+'\\')&&!OUT.startsWith(ROOT+'/'))throw Error('输出必须在工程内');
if(existsSync(join(OUT,'bundle.json')))throw Error('拒绝覆盖冻结候选');
mkdirSync(OUT,{recursive:true});
const SHA=b=>createHash('sha256').update(b).digest('hex');
const UPSTREAM='a84159688af3ca37a4be05a0d422b94451b2e24e';
const PAL=fit(['#123f73','#176e9a','#209dbe','#48cbdc','#8cecf1','#c5ffff','#efffff','#ffffff'],8);
const SIZE=[336,80],ANCHOR=[16,40],LENGTH=300,SEED=721102;
function hash(n){n=(n^SEED)>>>0;n=Math.imul(n^(n>>>16),0x7feb352d);n=Math.imul(n^(n>>>15),0x846ca68b);return((n^(n>>>16))>>>0)/4294967295;}
function noise(x,salt){let k=Math.floor(x),u=x-k;u=u*u*(3-2*u);return hash(k+salt)*(1-u)+hash(k+1+salt)*u;}
function shape(x,t){
  // 两个不同比例的非周期域，低频域扰动坐标；没有正弦细线或等距环。
  const warp=(noise((x-t*19)/51,77)-.5)*35;
  const a=noise((x+warp-t*12)/17,191),b=noise((x+warp+t*7)/8.3,607);
  return {center:(noise((x+warp-t*9)/29,431)-.5)*3.6,
    radius:7.3+4.8*a+2.6*b,rough:noise((x-t*13)/3.7,991)};
}
function drawBeam(p,t,strength,after=false){
  const pulses=[[-62+t*26,23,1.2],[49+t*18,13,.7],[204+t*11,19,.9]];
  for(let x=0;x<LENGTH;x++){
    const f=shape(x,t),edge=Math.min(1,(x+3)/10,(LENGTH-x)/12);
    const pulse=pulses.reduce((sum,[c,w,v])=>sum+Math.exp(-(((x-c)/w)**2))*v,0);
    const radius=(f.radius+Math.min(pulse,1.6)*2.1)*edge;
    for(let y=-23;y<=23;y++){
      const d=Math.abs(y-f.center),q=d/Math.max(.5,radius);
      if(q>1.65)continue;
      let level=q<.28?7:q<.52?6:q<.77?5:q<1?3:2;
      let alpha=q<=.77?1:q<=1?.82:(1.65-q)*.39;
      if(q>.82&&f.rough<.25)alpha*=.42;
      if(after){level=Math.min(level,5);alpha*=.44;}
      p.blend(x,y,PAL[level],alpha*strength);
    }
    // 软光直接用透明light buffer，composite(null)导出直通RGBA。
    if(x%3===0)p.glow(x,f.center,6+radius*.6,PAL[3],.10*strength*edge);
  }
  // 非等距、寿命交叠的短湍流羽；每枚独立宽度/偏移，不循环短片。
  for(let k=0;k<17;k++){
    const born=hash(k+1201)*9-2,age=t-born;
    if(age<0||age>4.5)continue;
    const x=hash(k+2201)*245+12+age*(5+hash(k+3201)*9);
    if(x>292)continue;
    const sign=hash(k+4201)>.5?1:-1,life=1-age/4.5;
    const radius=shape(x,t).radius;
    const y=sign*(radius-1+age*.8),reach=5+hash(k+5201)*11;
    const pts=[[x-reach,y*.64],[x-reach*.28,y+sign*2],[x,y],[x+2,y*.7]];
    p.polyline(pts,PAL[4],Math.min(1,strength*life*.7));
    p.glow(x-2,y,3.5,PAL[3],.18*strength*life);
  }
  // 掌前局部喷口；起点固定在真实独立根点，绝不添加周身Q环。
  if(!after){p.glow(1,0,11,PAL[4],.37*strength);p.disc(1,0,3.5,PAL[6],.8*strength);p.disc(1,0,1.5,PAL[7],strength);}
}
const specs=[
 {id:'seven_shake_pixelfx_beam',count:12,ticks:1,expiry_effect:'seven_shake_pixelfx_end',expiry_ticks:12,
  draw:(p,t)=>drawBeam(p,t,[.75,.90,1,1,.98,.99,.92,.83,.66,.47,.27,.10][t])},
 {id:'seven_shake_pixelfx_end',count:4,ticks:1,
  draw:(p,t)=>{if(t<3)drawBeam(p,t+12,[.12,.065,.025][t],true);}},
];
const catalog={},exports=[];
for(const spec of specs){
 const [w,h]=SIZE,cols=4,rows=Math.ceil(spec.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4);
 const folder=join(OUT,spec.id);mkdirSync(folder,{recursive:true});
 const rects=[],frames=[],phaseHashes=[],pngHashes=[];
 for(let i=0;i<spec.count;i++){
  const frame=createFrame(w,h),p=painterFor(frame).place(...ANCHOR);spec.draw(p,i);
  const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);
  for(let j=0;j<rgba.length;j+=4)if(rgba[j+3]<3)rgba.fill(0,j,j+4);
  const x=(i%cols)*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const png=encodePNG(w,h,rgba),name=String(i).padStart(2,'0')+'.png';
  writeFileSync(join(folder,name),png);phaseHashes.push(SHA(rgba));pngHashes.push(SHA(png));rects.push([x,y,w,h]);
  frames.push({filename:name,frame:{x,y,w,h},rotated:false,trimmed:false,spriteSourceSize:{x:0,y:0,w,h},sourceSize:{w,h},duration:1000/60});
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 writeFileSync(join(folder,'aseprite.json'),JSON.stringify({frames,meta:{app:'https://github.com/patch-gg/pixelfx',image:'atlas.png',format:'RGBA8888',size:{w:w*cols,h:h*rows},scale:'1',frameTags:[{name:spec.id,from:0,to:spec.count-1,direction:'forward'}],pixelfx:{fps:60,loop:false,pivot:ANCHOR,frames:spec.count,frameSize:SIZE}}},null,2)+'\n');
 catalog[spec.id]={id:spec.id,texture:`res://assets/effects/ultraseven/seven-shake-pixelfx-20261102-v1/${spec.id}/atlas.png`,rects,anchor:ANCHOR,ticks:1,loop:false,display_scale:[1,1],visual_scale:1,full_frame:true,emission_anchor:true,source_kind:'pixelfx_code_baked',license:'MIT',upstream_commit:UPSTREAM,authoring_source:'res://tools/rebuild/ultraseven/seven-shake-pixelfx-20261102-v1/bake.mjs',...(spec.expiry_ticks?{expiry_ticks:spec.expiry_ticks,expiry_effect:spec.expiry_effect}:{})};
 exports.push({id:spec.id,phases:spec.count,phase_rgba_sha256:phaseHashes,phase_png_sha256:pngHashes,atlas_sha256:SHA(png),rgba_straight_alpha:true});
}
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.bake.v1',art_source:'code',route:'PixelFX offline',seed:SEED,length:LENGTH,canvas:SIZE,anchor:ANCHOR,upstream_commit:UPSTREAM,source_sha256:SHA(readFileSync(SELF)),license_sha256:SHA(readFileSync(join(ROOT,'third_party/pixelfx/LICENSE'))),upstream:'https://github.com/patch-gg/pixelfx/tree/'+UPSTREAM,exports},null,2)+'\n');
console.log(JSON.stringify({output:OUT,exports:exports.map(e=>({id:e.id,phases:e.phases}))}));
