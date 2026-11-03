// PixelFX MIT: original UFEneo violet blade accents, offline RGBA pixel frames.
// Copyright (c) 2026 Patch and Hugo Duprez, upstream a84159688af3ca37a4be05a0d422b94451b2e24e.
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { createFrame, painterFor, composite, WHITE, TAU, Rng, fit } from '../../../third_party/pixelfx/src/core/index.js';
import { encodePNG } from '../../../third_party/pixelfx/tools/lib/png.mjs';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const arg=process.argv.indexOf('--out'); if(arg<0)throw Error('需要新 --out');
const OUT=resolve(ROOT,process.argv[arg+1]);if(!OUT.startsWith(ROOT+'/')&&!OUT.startsWith(ROOT+'\\'))throw Error('工程内候选');
if(existsSync(join(OUT,'bundle.json')))throw Error('不覆盖冻结烘焙');mkdirSync(OUT,{recursive:true});
const H=b=>createHash('sha256').update(b).digest('hex');
const C=fit(['#26133f','#50337e','#804fae','#b881e5','#dbb0ff','#f2dfff','#ffffff'],7);

function summon(p,i){
  const u=i/8, fade=Math.sin(Math.PI*(i+1)/9), radius=3+u*4;
  p.glow(0,0,15,C[3],.45*fade);
  for(let a=0;a<TAU;a+=.035){
    const q=(a/TAU*9+u*2)%1;
    if(q>.82)continue;
    p.dot(Math.cos(a)*radius,Math.sin(a)*radius*.7,q<.18?WHITE:C[4],fade);
  }
  const rng=new Rng(1913);
  for(let k=0;k<11;k++){
    const a=rng.range(-Math.PI,Math.PI),d=2+u*rng.range(8,17);
    p.dot(Math.cos(a)*d,Math.sin(a)*d,C[k%2+4],fade*(1-u*.7));
  }
}
function slash(p,i,dx,dy,seed){
  const n=Math.hypot(dx,dy),px=-dy/n,py=dx/n,fade=[.55,1,.62,.28][i];
  // 直接在最终朝向/跨度上离线写像素，运行不旋转、不拉伸、不复制第二把武器。
  for(let s=0;s<3;s++){
    const offset=(s-1)*3;
    for(let q=0;q<=n;q++){
      const t=q/n, bend=Math.sin(t*Math.PI)*(2+i*.9),x=dx*t+px*(offset+bend),y=dy*t+py*(offset+bend);
      const power=Math.sin(Math.PI*t)*fade;
      if(power>.15&&((q+i+s)%7<5))p.dot(x,y,C[3+s],power);
    }
  }
  p.glowLine(0,0,dx,dy,5,C[3],.24*fade);
  const rng=new Rng(seed);
  for(let k=0;k<16;k++){
    const t=rng.range(.1,.96),d=(i+1)*rng.range(1,2.5),side=k%2?1:-1;
    const x=dx*t+px*d*side,y=dy*t+py*d*side;
    const life=1-t*.45;
    p.line(x,y,x+dx/n*(2+k%3),y+dy/n*(2+k%3),k%4===0?WHITE:C[4],life*fade);
  }
}
function impact(p,i,guard){
  const end=guard?12:17,u=i/end;if(i>=end)return;
  const rng=new Rng(guard?1922:1921),flash=Math.max(0,1-i/4);
  if(flash){
    p.glow(0,0,26,C[3],flash*.75);p.circle(0,0,2+flash*3,C[5]);p.circle(0,0,2,WHITE);
    for(let k=0;k<9;k++){
      const a=k/9*TAU+rng.range(-.18,.18),d=rng.range(9,24)*flash;
      p.line(Math.cos(a)*2,Math.sin(a)*2,Math.cos(a)*d,Math.sin(a)*d,k%2?C[4]:WHITE,flash);
    }
  }
  for(let k=0;k<(guard?13:25);k++){
    const a=guard?rng.range(1.9,4.4):rng.range(0,TAU),speed=rng.range(42,155),age=i/60,life=rng.range(.12,.30);
    if(age>=life)continue;
    const x=Math.cos(a)*speed*age,y=Math.sin(a)*speed*age+70*age*age;
    const f=1-age/life;
    p.line(x,y,x+Math.cos(a)*(2+3*f),y+Math.sin(a)*(2+3*f),f>.6?WHITE:C[4],f);
    p.glow(x,y,3,C[2],f*.22);
  }
  if(guard&&i<7)for(let a=-1.05;a<=1.05;a+=.04){
    const rad=8+i*1.4;p.dot(-Math.cos(a)*rad,Math.sin(a)*rad,C[i<3?5:3],1-i/8);
  }
}
function landing(p,i){
  const u=i/12,rng=new Rng(1931),fade=1-u;
  if(i<3)p.glow(0,-2,19,C[3],(1-i/3)*.5);
  for(let k=0;k<24;k++){
    const side=k%2?1:-1,age=i/60,speed=rng.range(60,220),lift=rng.range(15,75);
    const x=side*(3+speed*age),y=-Math.max(0,lift*age-180*age*age);
    const length=1+Math.floor(rng.range(1,6)*fade);
    p.line(x,y,x+side*length,y-1,k%4===0?C[5]:C[2+k%2],fade*.75);
    if(k<8)p.glow(x,y,5,C[2],fade*.13);
  }
}
const specs=[
 {id:'teo_leapblade_summon',size:[48,48],anchor:[24,24],count:8,ticks:1,draw:summon},
 {id:'teo_leapblade_rise',size:[128,128],anchor:[36,88],count:4,ticks:1,draw:(p,i)=>slash(p,i,45,-45,1915)},
 {id:'teo_leapblade_cross',size:[144,64],anchor:[24,32],count:4,ticks:1,draw:(p,i)=>slash(p,i,94,2,1916)},
 {id:'teo_leapblade_descend',size:[128,144],anchor:[32,32],count:4,ticks:1,draw:(p,i)=>slash(p,i,44,63,1917)},
 {id:'teo_leapblade_hit',size:[112,112],anchor:[56,56],count:18,ticks:1,draw:(p,i)=>impact(p,i,false)},
 {id:'teo_leapblade_guard',size:[96,96],anchor:[48,48],count:13,ticks:1,draw:(p,i)=>impact(p,i,true)},
 {id:'teo_leapblade_landing',size:[144,64],anchor:[72,48],count:12,ticks:1,draw:landing},
];
const catalog={},exports=[];
for(const s of specs){
 const [w,h]=s.size,cols=Math.min(4,s.count),rows=Math.ceil(s.count/cols),atlas=new Uint8ClampedArray(w*cols*h*rows*4),rects=[],phases=[];
 const folder=join(OUT,s.id);mkdirSync(folder,{recursive:true});
 for(let i=0;i<s.count;i++){
  const f=createFrame(w,h),p=painterFor(f).place(...s.anchor);s.draw(p,i);const rgba=composite(f,new Uint8ClampedArray(w*h*4),null);
  for(let q=0;q<rgba.length;q+=4)if(rgba[q+3]<3)rgba.fill(0,q,q+4);
  const x=(i%cols)*w,y=Math.floor(i/cols)*h;
  for(let line=0;line<h;line++)atlas.set(rgba.subarray(line*w*4,(line+1)*w*4),((y+line)*w*cols+x)*4);
  rects.push([x,y,w,h]);phases.push(H(rgba));writeFileSync(join(folder,`${String(i).padStart(2,'0')}.png`),encodePNG(w,h,rgba));
 }
 const png=encodePNG(w*cols,h*rows,atlas);writeFileSync(join(folder,'atlas.png'),png);
 catalog[s.id]={id:s.id,texture:`res://assets/effects/ultraman-teo/${s.id}/atlas.png`,rects,anchor:s.anchor,ticks:s.ticks,loop:false,visual_scale:1,display_scale:[1,1],emission_anchor:true,source_kind:'pixelfx_code_baked',license:'MIT',upstream_commit:'a84159688af3ca37a4be05a0d422b94451b2e24e'};
 exports.push({id:s.id,phases:s.count,phase_hashes:phases,atlas_sha256:H(png),rgba_straight_alpha:true});
}
writeFileSync(join(OUT,'catalog.json'),JSON.stringify(catalog,null,2)+'\n');
writeFileSync(join(OUT,'bundle.json'),JSON.stringify({schema:'ufeneo.pixelfx.teo-leapblade.v1',source_sha256:H(readFileSync(fileURLToPath(import.meta.url))),upstream:'https://github.com/patch-gg/pixelfx/tree/a84159688af3ca37a4be05a0d422b94451b2e24e',exports},null,2)+'\n');
console.log(JSON.stringify({output:OUT,effects:exports.map(e=>({id:e.id,phases:e.phases}))}));
