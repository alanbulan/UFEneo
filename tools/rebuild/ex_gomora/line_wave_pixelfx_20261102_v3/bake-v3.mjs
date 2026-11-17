// EX Gomora 6I: whole native turbulent pressure volume, offline PixelFX raster bake.
// patch-gg/pixelfx a84159688af3ca37a4be05a0d422b94451b2e24e, MIT.
// Copyright (c) 2026 Patch and Hugo Duprez; licence and source snapshot accompany the export.
// Only the effect is authored here. No actor, rig, network or runtime JavaScript.
import {mkdirSync, existsSync, readFileSync, writeFileSync, copyFileSync} from 'node:fs';
import {resolve, join, dirname, relative, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createFrame, painterFor, composite} from '../../../../third_party/pixelfx/src/core/fx.js';
import {fit} from '../../../../third_party/pixelfx/src/core/color.js';
import {Rng, noise, noise2, fbm, smooth, clamp} from '../../../../third_party/pixelfx/src/core/math.js';
import {encodePNG} from '../../../../third_party/pixelfx/tools/lib/png.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
const flag=process.argv.indexOf('--out');
if(flag<0 || !process.argv[flag+1]) throw new Error('需要--out独立新候选目录');
const OUT=resolve(ROOT,process.argv[flag+1]), rel=relative(ROOT,OUT);
if(rel.startsWith('..') || isAbsolute(rel) || !rel.startsWith(join('art','fighters','ex_gomora')))
  throw new Error('只写本人art候选目录');
if(existsSync(OUT)) throw new Error('不覆盖旧烘焙目录');
const H=v=>createHash('sha256').update(v).digest('hex');
const upstreamPath=join(ROOT,'third_party/pixelfx/UPSTREAM.json');
const upstream=JSON.parse(readFileSync(upstreamPath,'utf8'));
const commit='a84159688af3ca37a4be05a0d422b94451b2e24e';
if(upstream.commit!==commit || upstream.license!=='MIT') throw new Error('固定上游身份不符');
for(const file of upstream.subset)
  if(H(readFileSync(join(ROOT,'third_party/pixelfx',file.path)))!==file.sha256)
    throw new Error('上游字节改变：'+file.path);
mkdirSync(OUT,{recursive:true});
copyFileSync(join(ROOT,'third_party/pixelfx/LICENSE'),join(OUT,'LICENSE.pixelfx.txt'));
copyFileSync(join(ROOT,'third_party/pixelfx/NOTICE.md'),join(OUT,'NOTICE.pixelfx.md'));
copyFileSync(fileURLToPath(import.meta.url),join(OUT,'authoring-source.mjs'));

const ID='ex_gomora_line_flight', CELL=[384,160], PIVOT=[24,80], SPAN=336, COUNT=8;
const SEED=661039;
const C=fit(['#61251f','#9d3b20','#d65c21','#f58b29','#ffbb48','#ffdc7d','#fff0b4','#fff8df'],8);
const opacity=[.78,1,.98,.94,.84,.70,.52,.32];
const coreRadius=x=>(7+25*smooth(0,105,x))*(1-.55*smooth(270,338,x));

// These uneven overlapping pressure parcels never draw a geometric outline.
// They only modulate the filled, shaded scalar volume; the visible faces are broken by advection.
const parcelRng=new Rng(SEED),parcels=[];
for(let i=0;i<12;i++) parcels.push({
  x:parcelRng.range(-45,345), y:parcelRng.range(-19,19),
  rx:parcelRng.range(17,43), ry:parcelRng.range(9,22),
  speed:parcelRng.range(14,24), heat:parcelRng.range(.55,1),
});

function volume(p,phase){
  // The scalar field is sampled on 2px clusters, then shaded in three unequal scales.
  // No sine, ring, repeating arc, closed outline or equal-distance band is used.
  p.each(0,-61,SPAN-1,61,(x,y,sx,sy)=>{
    const bx=Math.floor(x/2)*2+1, by=Math.floor(y/2)*2+1;
    const adv=bx-phase*21, grow=smooth(0,65,x);
    const centre=(noise(adv/53,SEED+7)*5+noise((bx+phase*4)/113,SEED+19)*2)*grow;
    const radius=coreRadius(x)+(noise(adv/31,SEED+31)*5+noise(adv/79,SEED+39)*3)*grow;
    const warpedX=adv+noise2(adv/37,by/27,SEED+41)*11;
    const warpedY=by-centre+noise2(adv/57,by/19,SEED+43)*6*grow;
    const cloud=fbm(warpedX/29,warpedY/18,SEED+47,3);
    const detail=noise2(warpedX/8,warpedY/8,SEED+53);
    const q=Math.abs(by-centre)/Math.max(5,radius);
    const boundary=1+cloud*.18+detail*.045;
    if(q>boundary+.23)return;

    // True translucent amber air around the opaque chunky middle, never a Bayer mesh.
    const rim=clamp((boundary+.23-q)/.25);
    if(q>boundary){
      p.blendPx(sx,sy,C[2],rim*.20);
      p.add(sx,sy,C[3],rim*.045);
      return;
    }
    let pressure=0;
    for(const parcel of parcels){
      const cx=parcel.x+phase*parcel.speed;
      const dx=(bx-cx)/parcel.rx;
      const dy=(warpedY-parcel.y*grow)/parcel.ry;
      const d=dx*dx+dy*dy;
      if(d<1.2)pressure=Math.max(pressure,(1-d)*parcel.heat);
    }
    const mass=clamp(1-q+cloud*.29+detail*.07);
    const face=noise2(warpedX/24+cloud*.8,warpedY/11,SEED+67);
    // Warm shadow pockets, broad lit gold faces and short cream fragments.
    // There is no unbroken white or yellow centre line.
    const heat=clamp(.19+mass*.32+pressure*.29+face*.17+cloud*.16);
    let level=Math.floor(heat*8);
    if(q>.85)level=Math.min(level,2);
    else if(q>.68)level=Math.min(level,3);
    if(face>.26 && mass>.30 && cloud>.10)level=Math.max(level,5);
    if(pressure>.58 && face>.15 && detail>.12)level=6;
    if(pressure>.76 && face>.32 && detail>.30)level=7;
    level=clamp(level,0,7);
    const edgeAlpha=q>.80?.72:q>.64?.88:1;
    p.blendPx(sx,sy,C[level],edgeAlpha);
    const lit=level>=5?.16:level>=3?.065:.018;
    p.add(sx,sy,C[4],lit*(1-q*.45));
  });

  // Coherent shards travel forward and peel from different sides at unequal speeds.
  const sparks=new Rng(SEED+100);
  for(let i=0;i<24;i++){
    const start=sparks.range(7,262), speed=sparks.range(6,23);
    const x=start+phase*speed;
    const side=sparks.sign(), offset=sparks.range(.82,1.25);
    const y=side*(coreRadius(x)*offset+phase*phase*sparks.range(.015,.08));
    const length=sparks.range(3,10), width=sparks.range(1,2);
    if(x+length>=SPAN-7 || Math.abs(y)>57)continue;
    p.beam(x,y,x+length,y+side*sparks.range(-1,2),width,C[3+i%3]);
    p.glow(x+length,y,3,C[4],.13);
  }
  // A small irregular hot contact joins the native abdominal point, without a charge circle.
  p.shade(-5,-7,18,7,(x,y,o)=>{
    const width=6*(1-clamp((x+2)/25))+.7;
    const off=noise((x+phase*2)/7,SEED+211)*1.2;
    const d=Math.abs(y-off)/width;
    if(d>1)return;
    o.c=C[d<.3?6:d<.65?5:3];
    o.k=d<.65?.14:.04;o.l=C[4];
  });
  p.glow(2,0,15,C[4],.14);
}

const columns=4,rows=2,atlas=new Uint8ClampedArray(CELL[0]*columns*CELL[1]*rows*4);
const frames=[],rects=[];
for(let index=0;index<COUNT;index++){
  const frame=createFrame(...CELL),p=painterFor(frame).place(...PIVOT);
  volume(p,index);
  const rgba=composite(frame,new Uint8ClampedArray(CELL[0]*CELL[1]*4),null);
  for(let y=0;y<CELL[1];y++)for(let x=0;x<CELL[0];x++){
    const q=(y*CELL[0]+x)*4,localX=x-PIVOT[0],localY=y-PIVOT[1];
    if(localX<-14 || localX>=SPAN || Math.abs(localY)>64){rgba.fill(0,q,q+4);continue;}
    // Temporal decay is real PNG alpha, not palette thinning through ordered dithering.
    const tip=1-smooth(324,336,localX);
    rgba[q+3]=Math.floor(rgba[q+3]*opacity[index]*tip);
    if(rgba[q+3]<3)rgba.fill(0,q,q+4);
  }
  const x=index%columns*CELL[0],y=Math.floor(index/columns)*CELL[1];
  for(let row=0;row<CELL[1];row++)atlas.set(rgba.subarray(row*CELL[0]*4,(row+1)*CELL[0]*4),((y+row)*CELL[0]*columns+x)*4);
  const png=encodePNG(...CELL,rgba),name=String(index).padStart(2,'0')+'.png';
  writeFileSync(join(OUT,name),png);frames.push({index,file:name,sha256:H(png),rgba_sha256:H(rgba),opacity:opacity[index]});
  rects.push([x,y,...CELL]);
}
const atlasPng=encodePNG(CELL[0]*columns,CELL[1]*rows,atlas);
writeFileSync(join(OUT,'atlas.png'),atlasPng);
const sourcePath=relative(ROOT,fileURLToPath(import.meta.url)).replaceAll('\\','/');
const clip={
  texture:'res://assets/effects/ex_gomora/line_wave_pixelfx_20261102_v3/atlas.png',rects,cell:CELL,
  frames:COUNT,ticks:1,anchor:PIVOT,emission_anchor:true,full_frame:true,
  display_scale:[1,1],visual_scale:1,loop:false,orientation:'authored',
  source_kind:'pixelfx_code_baked',authoring_source:sourcePath,
  license:'MIT',upstream_commit:commit,atlas_sha256:H(atlasPng),
  behind_fighter:false,color_parameter:false,
  native_forward_span:SPAN,simulation_length_unchanged:336,simulation_life_unchanged:8,
  approved:false,review_status:'v3厚芯体积离线候选；待根正式main/双向/原输入回放受托验收'
};
writeFileSync(join(OUT,'catalog-candidate.json'),JSON.stringify({[ID]:clip},null,2)+'\n');
const provenance={schema:'ufeneo.pixelfx.ex-gomora-line-wave.v3',effect:ID,source:sourcePath,
  source_sha256:H(readFileSync(fileURLToPath(import.meta.url))),source_snapshot:'authoring-source.mjs',
  source_snapshot_sha256:H(readFileSync(join(OUT,'authoring-source.mjs'))),
  upstream_repo:upstream.repo,upstream_commit:commit,
  upstream_manifest_sha256:H(readFileSync(upstreamPath)),upstream_subset_verified:true,
  license:'MIT',license_sha256:H(readFileSync(join(OUT,'LICENSE.pixelfx.txt'))),
  notice_sha256:H(readFileSync(join(OUT,'NOTICE.pixelfx.md'))),
  actual_library_calls:['createFrame','painterFor/place','Painter.each/blendPx/add/shade/beam/glow','Rng','noise/noise2/fbm/smooth','fit','composite','encodePNG'],
  seed:SEED,cell:CELL,anchor:PIVOT,native_forward_span:SPAN,frames,
  atlas_sha256:H(atlasPng),straight_rgba:true,whole_effect_frames:true,
  design:'金橙不规则压力体积：连续厚芯、错位受光块、非等距湍流、短向前碎屑；无正弦/圆环/连续细轮廓；尾相整块真Alpha渐隐',
  no_network:true,no_actor_png_read:true,no_rig_rendered:true,no_old_fx_png_read:true,
  no_runtime_javascript:true,no_q_attachments:true,installed:false,
  clock_boundary:'原模拟spawn age0后同step advance至1，life8保持；正常live age1..7，不为播齐相0改时钟'};
writeFileSync(join(OUT,'provenance.json'),JSON.stringify(provenance,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({...provenance,catalog_sha256:H(readFileSync(join(OUT,'catalog-candidate.json')))},null,2)+'\n');
console.log(JSON.stringify({out:OUT,atlas_sha256:H(atlasPng),phases:COUNT,native_forward_span:SPAN,installed:false}));
