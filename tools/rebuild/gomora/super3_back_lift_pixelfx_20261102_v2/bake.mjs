// Physical layered back-lift dust v2, actual fixed MIT PixelFX offline raster baking.
import {mkdirSync,existsSync,readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import {resolve,join,dirname,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createFrame,painterFor,composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {Rng} from '../../../../third_party/pixelfx/src/core/math.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const at=process.argv.indexOf('--out');if(at<0)throw Error('需要新 --out');
const OUT=resolve(ROOT,process.argv[at+1]),allowed=resolve(ROOT,'art/fighters/gomora/stage4/super3-back-lift-pixelfx-v2');
const sub=relative(allowed,OUT);if(!sub||sub.startsWith('..')||isAbsolute(sub)||existsSync(OUT))throw Error('只可写本人v2新分支，不覆盖');
const H=b=>createHash('sha256').update(b).digest('hex');
const rel=p=>relative(ROOT,p).replaceAll('\\','/'),record=p=>({path:rel(p),sha256:H(readFileSync(p))});
const up=join(ROOT,'third_party/pixelfx/UPSTREAM.json'),upstream=JSON.parse(readFileSync(up,'utf8'));
if(upstream.commit!=='a84159688af3ca37a4be05a0d422b94451b2e24e')throw Error('固定MIT提交漂移');
const checked=upstream.subset.map(r=>{const p=join(ROOT,'third_party/pixelfx',r.path);if(H(readFileSync(p))!==r.sha256)throw Error('上游源漂移 '+r.path);return record(p);});
const contractPath=join(ROOT,'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1/new-whole-frame-contract.json');
if(H(readFileSync(contractPath))!=='335500068e8559c65903c27576baef22b2129b55b20fc96c108d38a68b909a9d')throw Error('冻结合同漂移');
mkdirSync(OUT,{recursive:true});
copyFileSync(join(ROOT,'third_party/pixelfx/LICENSE'),join(OUT,'LICENSE.pixelfx.txt'));
copyFileSync(join(ROOT,'third_party/pixelfx/NOTICE.md'),join(OUT,'NOTICE.pixelfx.md'));
const HEX=['#47372b','#68503a','#8f6c45','#b28d58','#cfb47c','#e4d5ac'];const C=fit(HEX,6);
const PARAMETERS={version:2,tick_rate:60,palette:HEX,alpha:'PixelFX binary ordered dither; no glow buffer',
 capture:{seed:2026110241,count:5,ticks_per_phase:1,fade:[1,.9,.62,.28,0]},
 release:{seed:2026110242,count:7,ticks_per_phase:2,width:[14,31,46,54,57,53,0],height:[6,9,14,17,17,14,0],fade:[.85,1,1,.9,.65,.32,0]},
 landing:{seed:2026110243,count:8,ticks_per_phase:2,width:[24,57,82,90,88,84,77,0],height:[8,18,24,26,23,18,13,0],fade:[1,1,1,1,.84,.56,.26,0]},
 independent_whole_rgba_geometry:true,no_previous_png_read:true,no_circle_or_ring:true,no_hitboxes:true,
 v1_kept:'art/fighters/gomora/stage4/super3-back-lift-pixelfx-v1'};
// A jagged filled dust lobe with four stepped values. No outlined circle or magical ring.
function lobe(p,cx,base,rx,rise,fade,salt){
 const outline=[[-1,0],[-1,-.22],[-.87,-.24],[-.87,-.51],[-.62,-.54],[-.62,-.8],[-.31,-.79],[-.22,-1],
  [.12,-1],[.28,-.83],[.59,-.87],[.72,-.63],[.92,-.56],[.92,-.3],[1,-.27],[1,0]];
 const pts=outline.map(([x,y])=>[cx+x*rx,base+y*rise]);p.poly(pts,C[0],fade);
 const inner=[[-.85,-.11],[-.82,-.37],[-.52,-.46],[-.49,-.69],[-.13,-.74],[.12,-.91],[.39,-.7],[.63,-.63],[.83,-.37],[.78,-.12]];
 p.poly(inner.map(([x,y])=>[cx+x*rx,base+y*rise]),C[1],fade);
 p.poly([[-.69,-.38],[-.53,-.6],[-.23,-.63],[-.13,-.82],[.11,-.82],[.31,-.61],[.55,-.59],[.62,-.42],[.32,-.33],[-.05,-.39]]
  .map(([x,y])=>[cx+x*rx,base+y*rise]),C[2],fade);
 p.poly([[-.5,-.5],[-.3,-.64],[-.12,-.65],[-.06,-.79],[.1,-.76],[.25,-.58],[.07,-.52],[-.07,-.55]]
  .map(([x,y])=>[cx+x*rx,base+y*rise]),C[3],fade*.95);
 if(rise>10){p.line(cx-rx*.4,base-rise*.6,cx-rx*.12,base-rise*.68,C[4],fade*.7);}
 // Deterministic gaps separate inner volume levels; dither fade prevents a hard cut.
 if(salt%2===0)p.line(cx+rx*.42,base-rise*.26,cx+rx*.68,base-rise*.28,C[0],fade*.8);
}
function capture(p,i){
 if(i===4)return;const fade=PARAMETERS.capture.fade[i],R=new Rng(PARAMETERS.capture.seed),t=i/60;
 if(i<2){p.line(-4,-1,-1,1,C[5],fade);p.line(1,1,4,-1,C[3],fade);p.dot(0,0,C[5],fade);}
 for(let k=0;k<12;k++){
  const s=k%2?-1:1,x=s*(R.range(.3,2)+R.range(30,95)*t),y=R.range(-1,1)+R.range(-55,46)*t+70*t*t;
  if(t>=R.range(.045,.08))continue;p.dot(x,y,C[2+k%3],fade);
  if(i<2&&k%4===0)p.dot(x+s,y,C[4],fade*.8);
 }
}
function release(p,i){
 if(i===6)return;const o=PARAMETERS.release,w=o.width[i],h=o.height[i],fade=o.fade[i],R=new Rng(o.seed);
 // Three distinct trailing volumes, the longest at rear LEFT. Front/root stays open for the actor.
 const leading=-3-w*.23,mid=-3-w*.52,trail=-3-w*.76;
 lobe(p,leading,-1,w*.2,h*.62,fade,1);
 lobe(p,mid,-3,w*.22,h*.86,fade*.9,2);
 lobe(p,trail,-5,w*.18,h*.62,fade*.8,3);
 for(let k=0;k<15;k++){
  const x=-R.range(.1,.95)*w,y=-R.range(0,h+3);
  if(i>3&&k%3===0)continue;p.dot(x,y,C[1+k%4],fade*.9);
 }
 if(i<4){p.line(-w*.22,-h*.65,-w*.38,-h*.83,C[4],fade*.7);p.line(-w*.62,-h*.65,-w*.77,-h*.8,C[3],fade*.65);}
}
function landing(p,i){
 if(i===7)return;const o=PARAMETERS.landing,w=o.width[i],h=o.height[i],fade=o.fade[i],R=new Rng(o.seed);
 // Low two-sided dust volume. Large shoulders go behind the victim; centre is shallow and open above.
 const radius=w*.235,centre=w*.255;
 lobe(p,-centre,0,radius,h,fade,2);lobe(p,centre,0,radius,h*.94,fade,3);
 if(i<4){
  lobe(p,-w*.13,1,w*.16,h*.52,fade,5);lobe(p,w*.13,1,w*.16,h*.5,fade,6);
 }
 // Short central physical contact glint, not a radiating star or spell.
 if(i<2){p.poly([[-5,-2],[-2,-4],[2,-4],[5,-2],[3,0],[-3,0]],C[4],fade);p.line(-2,-2,2,-2,C[5],fade);}
 if(i===2){p.line(-2,-1,2,-1,C[4],fade*.8);}
 // Irregular pebbles leave both sides and descend, constrained inside the agreed 95x28 envelope.
 for(let k=0;k<14;k++){
  const s=k%2?-1:1,u=i/6,x=s*(R.range(.25,.48)*w),y=-Math.min(h+1,Math.max(1,R.range(2,9)+Math.sin(u*Math.PI)*R.range(2,13)));
  const size=(i<4&&k%4===0)?2:1;p.rect(x,y,size,size,C[k%3],fade);
  if(i<4&&k%4===0)p.dot(x,y-1,C[4],fade*.8);
 }
}
const specs=[
 {id:'gomora_back_lift_capture_contact',size:[40,36],anchor:[20,18],o:PARAMETERS.capture,draw:capture,
  trigger:{event:'hit',move:'special3',move_kind:'throw',capture_confirmed:true,once:true,whiff:false},purpose:'轻量真实承接接触碎屑'},
 {id:'gomora_back_lift_release_dust',size:[96,64],anchor:[72,46],o:PARAMETERS.release,draw:release,
  trigger:{transition:'captured successful victim motion.throw_released false->true',once:true,whiff:false,existing_named_event:false},purpose:'40–60原生宽的分层后拖土尘，仍可看完整背部',layer_recommendation:'behind actor and victim'},
 {id:'gomora_back_lift_landing_dust',size:[128,64],anchor:[64,48],o:PARAMETERS.landing,draw:landing,
  trigger:{event:'throw_slam',move:'special3',once:true,whiff:false,not_capture_hit:true},purpose:'75–95宽、20–28高的低地两侧体积尘，中间短接触闪与落石',layer_recommendation:'volume behind victim; origin at actual ground contact'},
];
const effects=[],catalog={};
for(const spec of specs){
 const [w,h]=spec.size,cols=4,rows=Math.ceil(spec.o.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4),folder=join(OUT,spec.id);
 mkdirSync(folder);const frames=[],rects=[];
 for(let i=0;i<spec.o.count;i++){
  const frame=createFrame(w,h),p=painterFor(frame).place(...spec.anchor);spec.draw(p,i);
  const rgba=composite(frame,new Uint8ClampedArray(w*h*4),null);
  for(let q=0;q<rgba.length;q+=4)if(rgba[q+3]===0)rgba.fill(0,q,q+4);
  const x=i%cols*w,y=Math.floor(i/cols)*h;
  for(let row=0;row<h;row++)atlas.set(rgba.subarray(row*w*4,(row+1)*w*4),((y+row)*w*cols+x)*4);
  const path=join(folder,String(i).padStart(2,'0')+'.png');writeFileSync(path,encodePNG(w,h,rgba));frames.push({index:i,...record(path),rgba_sha256:H(rgba)});rects.push([x,y,w,h]);
 }
 const path=join(folder,'atlas.png');writeFileSync(path,encodePNG(w*cols,h*rows,atlas));
 effects.push({id:spec.id,size:spec.size,anchor:spec.anchor,seed:spec.o.seed,frames,atlas:record(path),last_frame_blank:true,
  purpose:spec.purpose,trigger_contract:spec.trigger,actual_attachment:null,layer_recommendation:spec.layer_recommendation??'physical capture intersection only'});
 catalog[spec.id]={id:spec.id,atlas_candidate:rel(path),runtime_texture:null,rects,cell:spec.size,anchor:spec.anchor,
  anchor_space:'FX自身独立根，尚未挂实际本人/受方世界点',ticks:spec.o.ticks_per_phase,loop:false,visual_scale:1,display_scale:[1,1],
  source_kind:'pixelfx_code_baked',license:'MIT',upstream_commit:upstream.commit,installed:false,collision:false,
  trigger_contract:spec.trigger,layer_recommendation:spec.layer_recommendation??'capture contact',attachment_status:'pending actual actor-victim geometry'};
}
writeFileSync(join(OUT,'parameters.json'),JSON.stringify(PARAMETERS,null,2)+'\n');
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.gomora-back-lift.v2',source:record(fileURLToPath(import.meta.url)),
 contract:record(contractPath),parameters:record(join(OUT,'parameters.json')),upstream:'https://github.com/patch-gg/pixelfx/tree/'+upstream.commit,
 upstream_commit:upstream.commit,upstream_manifest:record(up),upstream_checked:checked,license:record(join(OUT,'LICENSE.pixelfx.txt')),
 notice:record(join(OUT,'NOTICE.pixelfx.md')),actual_library_calls:['createFrame','painterFor/place','Painter.poly/line/rect/dot','composite','Rng','fit','encodePNG'],
 no_network:true,no_actor_or_rig_rendered:true,no_old_effect_png_read:true,no_ring_q_beam_wave:true,whole_rgba_frames:true,installed:false,effects},null,2)+'\n');
console.log(JSON.stringify({output:OUT,effects:effects.map(e=>({id:e.id,phases:e.frames.length,atlas_sha256:e.atlas.sha256}))}));
