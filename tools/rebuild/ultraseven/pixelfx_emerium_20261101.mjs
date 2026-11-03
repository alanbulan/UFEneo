// UFEneo 艾梅利姆试装：PixelFX 的像素/光缓冲离线烘焙，游戏只播放透明整帧。
// Banded beam, travelling pulses and strands adapted from patch-gg/pixelfx arcane-beam,
// and Sprite Fusion energy (https://www.spritefusion.com/pixel-art-vfx/energy).
// MIT License, Copyright (c) 2026 Patch and Hugo Duprez. See third_party/pixelfx/LICENSE.
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { createFrame, painterFor, composite, fit, WHITE, TAU, Rng } from '../../../third_party/pixelfx/src/core/index.js';
import { encodePNG } from '../../../third_party/pixelfx/tools/lib/png.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const outArg = process.argv.indexOf('--out');
if (outArg < 0) throw new Error('需要 --out 新候选目录');
const OUT = resolve(ROOT, process.argv[outArg + 1]);
if (!OUT.startsWith(ROOT + '/') && !OUT.startsWith(ROOT + '\\')) throw new Error('仅写工程内候选');
if (existsSync(join(OUT, 'bundle.json'))) throw new Error('不覆盖冻结候选');
mkdirSync(OUT, { recursive: true });
const C = fit(['#102c5e', '#1c5489', '#267da8', '#45b6d9', '#83e1ef', '#c2f5ff', '#edfeff', '#ffffff'], 8);
const hash = b => createHash('sha256').update(b).digest('hex');

function beam(p, phase, length, strength = 1) {
  const ph = phase / 8, w = 3.4 * strength;
  // 所有列在目标原生跨度上直接生成，整条光束没有中段重复/拉伸。
  for (let d = 0; d <= length; d++) {
    const taper = Math.min(1, (d + 2) / 7, (length - d + 2) / 5);
    const radius = Math.max(.65, w * taper * (1 + .13 * Math.sin(d * .14 - ph * TAU * 2)));
    const pulse = ((d / 55 - ph * 3) % 1 + 1) % 1 < .12;
    for (let y = -Math.ceil(radius * 1.5); y <= Math.ceil(radius * 1.5); y++) {
      const q = Math.abs(y) / radius;
      if (q > 1.45) continue;
      const level = q < .25 ? 7 : q < .55 ? 6 : q < .85 ? 4 : q < 1.1 ? 3 : 2;
      p.dot(d, y, C[Math.min(7, level + (pulse && q < 1 ? 1 : 0))], q > 1 ? .5 : 1);
    }
    for (let s = 0; s < 2; s++) {
      const a = d * .095 - ph * TAU * 2 + s * Math.PI;
      if (Math.cos(a) > 0) p.dot(d, Math.sin(a) * radius * 1.35, Math.cos(a) > .7 ? WHITE : C[5]);
    }
  }
  p.glowLine(1, 0, length - 1, 0, 8, C[4], .27 * strength);
  // 发射闪只在额灯中心，无吸入粒子、周身环或Q光效。
  const root = 2 + .5 * Math.sin(ph * TAU * 3);
  p.circle(1, 0, root, C[6]); p.circle(1, 0, 1.2, WHITE);
  p.glow(1, 0, 12, C[4], .43 * strength);
  for (let k = 0; k < 13; k++) {
    const x = ((k * 43 + phase * 19) % (length - 12)) + 6;
    const y = ((k & 1) ? 1 : -1) * (5 + ((k + phase) % 4));
    p.line(x, y, Math.min(length, x + 3 + (k % 4)), y, C[4 + (k % 2)], .65 * strength);
  }
}

function impact(p, phase, guard = false) {
  const duration = guard ? 14 : 18, u = phase / duration;
  if (phase >= duration) return;
  const r = new Rng(guard ? 714 : 711);
  const flash = Math.max(0, 1 - phase / 4);
  if (flash > 0) {
    if (!guard) {
      for (let ray = 0; ray < 11; ray++) {
        const a = ray * TAU / 11 + r.range(-.2, .2);
        const reach = r.range(11, 23) * (.5 + flash * .5);
        p.line(Math.cos(a) * 2, Math.sin(a) * 2, Math.cos(a) * reach, Math.sin(a) * reach,
          u => u < .45 ? WHITE : u < .75 ? C[6] : C[4], u => u < .6 ? flash : flash * .65);
      }
    }
    p.circle(0, 0, 3 + flash * 3, C[6]);
    p.circle(0, 0, 2 + flash * 1.5, WHITE);
    p.glow(0, 0, 25, C[4], flash * .8);
  }
  // 命中是向外喷散的破碎闪；防御是局部偏转弧，各有独立轮廓。
  for (let k = 0; k < (guard ? 14 : 23); k++) {
    const angle = guard ? r.range(-1.45, 1.45) + Math.PI : r.range(-Math.PI, Math.PI);
    const speed = r.range(42, guard ? 125 : 170), age = phase / 60;
    const life = r.range(.1, guard ? .24 : .32);
    if (age >= life) continue;
    const x = Math.cos(angle) * speed * age, y = Math.sin(angle) * speed * age + 45 * age * age;
    const size = (1 - age / life) * r.range(2, 5);
    p.line(x, y, x + Math.cos(angle) * size, y + Math.sin(angle) * size, age / life < .35 ? C[7] : C[5], 1 - u * .65);
    p.glow(x, y, 3, C[4], .23 * (1 - u));
  }
  if (guard && phase < 8) {
    const radius = 5 + phase * 1.6;
    for (let a = -.95; a <= .95; a += .035) {
      p.dot(-Math.cos(a) * radius, Math.sin(a) * radius * 1.15, phase < 3 ? C[6] : C[4], 1 - phase / 10);
    }
  }
}

const specs = [
  { id: 'seven_pixelfx_emerium_a', size: [512, 64], anchor: [24, 32], count: 8, ticks: 1, full_frame: true,
    draw: (p, i) => beam(p, i, 450, [.7, 1, 1, .95, 1, .9, .65, .32][i]) },
  { id: 'seven_pixelfx_emerium_start', size: [40, 40], anchor: [20, 20], count: 3, ticks: 1,
    draw: (p, i) => { p.glow(0, 0, 6 + i * 2, C[4], .15 + i * .1); p.circle(0, 0, 1 + i * .5, i === 2 ? WHITE : C[6]); } },
  { id: 'seven_pixelfx_emerium_end', size: [512, 64], anchor: [24, 32], count: 4, ticks: 1, full_frame: true,
    draw: (p, i) => { const k = (3 - i) / 4; if (k > 0) { p.fade = k; beam(p, i + 8, 450, .2 + k * .3); } } },
  { id: 'seven_pixelfx_emerium_hit', size: [112, 96], anchor: [56, 48], count: 19, ticks: 1,
    draw: (p, i) => impact(p, i, false) },
  { id: 'seven_pixelfx_emerium_guard', size: [96, 80], anchor: [48, 40], count: 15, ticks: 1,
    draw: (p, i) => impact(p, i, true) },
  { id: 'seven_pixelfx_emerium_air', size: [40, 40], anchor: [20, 20], count: 8, ticks: 2, loop: true, orientation: 'authored',
    draw: (p, i) => {
      // 原生斜向光弹直接写在像素网格，运行时不旋转横束。
      const tail = -8, head = 5, pulse = .6 + .4 * Math.sin(i / 8 * TAU);
      p.glowLine(tail, tail, head, head, 5, C[4], .4);
      for (let d = tail; d <= head; d++) {
        p.dot(d, d, WHITE); p.dot(d, d - 1, C[6]); p.dot(d - 1, d, C[5]);
        if ((d + i) % 4 !== 0) { p.dot(d + 1, d, C[4]); p.dot(d, d + 1, C[4]); }
      }
      p.circle(head, head, 1.5, C[6]); p.glow(head, head, 5, C[5], .3 * pulse);
    } },
];

const catalog = {}, exports = [];
for (const spec of specs) {
  const [w, h] = spec.size, cols = Math.min(4, spec.count), rows = Math.ceil(spec.count / cols);
  const atlas = new Uint8ClampedArray(w * cols * h * rows * 4), frames = [], rects = [], phaseHashes = [];
  const folder = join(OUT, spec.id); mkdirSync(folder, { recursive: true });
  for (let i = 0; i < spec.count; i++) {
    const f = createFrame(w, h), p = painterFor(f).place(...spec.anchor);
    spec.draw(p, i);
    const rgba = composite(f, new Uint8ClampedArray(w * h * 4), null);
    // Tiny light tails cannot leak into corners, nor carry hidden RGB into an alpha-zero texel.
    for (let q = 0; q < rgba.length; q += 4) if (rgba[q + 3] < 3) rgba.fill(0, q, q + 4);
    const x = (i % cols) * w, y = Math.floor(i / cols) * h;
    for (let line = 0; line < h; line++) atlas.set(rgba.subarray(line * w * 4, (line + 1) * w * 4), ((y + line) * w * cols + x) * 4);
    rects.push([x, y, w, h]); phaseHashes.push(hash(rgba));
    frames.push({ filename: `${spec.id} ${i}`, frame: { x, y, w, h }, rotated: false, trimmed: false,
      spriteSourceSize: { x: 0, y: 0, w, h }, sourceSize: { w, h }, duration: 1000 * spec.ticks / 60 });
    writeFileSync(join(folder, `${String(i).padStart(2, '0')}.png`), encodePNG(w, h, rgba));
  }
  const png = encodePNG(w * cols, h * rows, atlas); writeFileSync(join(folder, 'atlas.png'), png);
  const meta = { app: 'https://github.com/patch-gg/pixelfx', image: 'atlas.png', format: 'RGBA8888', size: { w: w * cols, h: h * rows }, scale: '1',
    frameTags: [{ name: spec.id, from: 0, to: spec.count - 1, direction: 'forward' }],
    pixelfx: { fps: 60 / spec.ticks, loop: !!spec.loop, columns: cols, pivot: spec.anchor, frames: spec.count, frameSize: spec.size } };
  writeFileSync(join(folder, 'aseprite.json'), JSON.stringify({ frames, meta }, null, 2) + '\n');
  const clip = { id: spec.id, texture: `res://assets/effects/ultraseven/${spec.id}/atlas.png`, rects, anchor: spec.anchor,
    ticks: spec.ticks, loop: !!spec.loop, visual_scale: 1, display_scale: [1, 1], emission_anchor: true,
    source_kind: 'pixelfx_code_baked', authoring_source: 'res://tools/rebuild/ultraseven/pixelfx_emerium_20261101.mjs',
    license: 'MIT', upstream_commit: 'a84159688af3ca37a4be05a0d422b94451b2e24e',
    ...(spec.full_frame ? { full_frame: true } : {}), ...(spec.orientation ? { orientation: spec.orientation } : {}) };
  if (spec.id === 'seven_pixelfx_emerium_a') Object.assign(clip, { expiry_ticks: 8, expiry_effect: 'seven_pixelfx_emerium_end' });
  catalog[spec.id] = clip; exports.push({ id: spec.id, phases: spec.count, phase_hashes: phaseHashes, atlas_sha256: hash(png), rgba_straight_alpha: true });
}
writeFileSync(join(OUT, 'catalog.json'), JSON.stringify(catalog, null, 2) + '\n');
writeFileSync(join(OUT, 'bundle.json'), JSON.stringify({ schema: 'ufeneo.pixelfx.bake.v1', seed: 711,
  source_sha256: hash(readFileSync(fileURLToPath(import.meta.url))), upstream: 'https://github.com/patch-gg/pixelfx/tree/a84159688af3ca37a4be05a0d422b94451b2e24e', exports }, null, 2) + '\n');
console.log(JSON.stringify({ output: OUT, exports: exports.map(x => ({ id: x.id, phases: x.phases })) }));
