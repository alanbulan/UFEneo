// 赛文艾梅利姆主束：PixelFX 离线烘焙的整相横束，游戏只播放透明整帧。
// 边缘按两段不同频率的扰动打碎，没有笔直的上下边、没有等距脉冲环。
// MIT License, Copyright (c) 2026 Patch and Hugo Duprez. See third_party/pixelfx/LICENSE.
import { createFrame, painterFor, composite, fit } from '../../../../third_party/pixelfx/src/core/index.js';
import { encodePNG } from '../../../../third_party/pixelfx/tools/lib/png.mjs';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const SELF = fileURLToPath(import.meta.url);
const ROOT = resolve(dirname(SELF), '../../../..');
const at = process.argv.indexOf('--out');
if (at < 0) throw Error('需要 --out 新候选目录');
const OUT = resolve(ROOT, process.argv[at + 1]);
if (!OUT.startsWith(ROOT + '/') && !OUT.startsWith(ROOT + '\\')) throw Error('只写工程内候选');
if (existsSync(join(OUT, 'bundle.json'))) throw Error('不覆盖冻结候选');
mkdirSync(OUT, { recursive: true });
const SHA = b => createHash('sha256').update(b).digest('hex');
const UPSTREAM = 'a84159688af3ca37a4be05a0d422b94451b2e24e';
const SEED = 20261117;
// 沿用已批准的艾梅利姆青白档，不另起色相。
const C = fit(['#102c5e', '#1c5489', '#267da8', '#45b6d9', '#83e1ef', '#c2f5ff', '#edfeff', '#ffffff'], 8);

const SIZE = [512, 96], ANCHOR = [20, 48], LENGTH = 452;
const COLS = 4, COUNT = 8, TICKS = 1;

function h(k, salt) {
  let n = (Math.imul(k | 0, 2654435761) ^ Math.imul(salt, 40503) ^ SEED) >>> 0;
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}
function noise(x, salt) {
  const k = Math.floor(x), u = x - k, s = u * u * (3 - 2 * u);
  return h(k, salt) * (1 - s) + h(k + 1, salt) * s;
}

// strength：该相的能量，起手最弱、中段最亮、末尾收细。
// 每列是实心的一条竖段：粗细随列变化做出阶梯边缘，不撒漫天的半透明噪点。
function beam(p, phase, strength) {
  const ph = phase / COUNT;
  for (let d = 0; d <= LENGTH; d++) {
    const taper = Math.min(1, (d + 5) / 14, (LENGTH - d + 5) / 16);
    // 慢频定粗细，快频只让边缘在 ±1 像素内咬合。
    const slow = noise(d / 41 - ph * 1.9, 311);
    const bite = noise(d / 7.3 + ph * 2.7, 977) - 0.5;
    const base = (3.2 + 1.7 * slow) * taper * (0.7 + strength * 0.55);
    const half = Math.max(0, Math.round(base + bite * 1.1));
    if (half <= 0) continue;
    // 脉冲不按等距排队：每相三个峰，峰位随相漂移。
    const knot = Math.max(
      1 - Math.abs(((d / 83 - ph * 1.35) % 1 + 1) % 1 - 0.5) * 2.4,
      1 - Math.abs(((d / 131 + 0.4 - ph * 1.1) % 1 + 1) % 1 - 0.5) * 2.4,
    );
    const hot = knot > 0.55;
    for (let y = -half; y <= half; y++) {
      const q = Math.abs(y) / half;
      let level = q < 0.2 ? 7 : q < 0.42 ? 6 : q < 0.68 ? 5 : q < 0.88 ? 4 : 3;
      if (hot) level = Math.min(7, level + 1);
      p.dot(d, y, C[level]);
    }
    // 被咬掉的那一像素只在少数列出现，形成参差的轮廓毛口。
    if (half >= 3 && h(d * 13 + phase * 97, 419) > 0.72) {
      p.dot(d, -half - 1, C[3]);
      if (h(d * 17 + phase * 61, 421) > 0.6) p.dot(d, half + 1, C[2]);
    }
  }
  // 根部：额灯位置的一小块亮点，带两根短须，不是正圆。
  const rootR = 2 + 1.6 * strength;
  for (let i = 0; i < 12; i++) {
    const a = h(i, 23) * Math.PI * 2;
    const rr = rootR * (0.55 + h(i, 29) * 0.8);
    p.dot(1 + Math.cos(a) * rr * 0.7, Math.sin(a) * rr, i < 4 ? C[7] : C[5]);
  }
  p.dot(0, 0, C[7]); p.dot(1, 0, C[7]); p.dot(0, 1, C[6]); p.dot(1, -1, C[6]);
  // 束身电离火花：极少量，位置每相不同，不排成直线。
  for (let k = 0; k < 9; k++) {
    const d = 10 + h(k, 71) * (LENGTH - 24);
    const side = h(k, 73) > 0.5 ? 1 : -1;
    const y = side * (5 + h(k, 79) * 3.2);
    p.dot(d, y, C[3]);
    if (h(k, 83) > 0.6) p.dot(d + 1, y + side, C[2]);
  }
}

const id = 'seven_beam_core';
const [w, hgt] = SIZE;
const rows = Math.ceil(COUNT / COLS);
const atlas = new Uint8ClampedArray(w * COLS * hgt * rows * 4);
const folder = join(OUT, id);
mkdirSync(folder, { recursive: true });
const rects = [], frames = [], phaseHashes = [];
const strength = [0.55, 0.8, 1, 1, 0.95, 0.85, 0.7, 0.5];
for (let i = 0; i < COUNT; i++) {
  const frame = createFrame(w, hgt);
  const p = painterFor(frame).place(...ANCHOR);
  beam(p, i, strength[i]);
  const rgba = composite(frame, new Uint8ClampedArray(w * hgt * 4), null);
  for (let q = 0; q < rgba.length; q += 4) if (rgba[q + 3] < 24) rgba.fill(0, q, q + 4);
  for (let q = 3; q < rgba.length; q += 4) rgba[q] = rgba[q] >= 128 ? 255 : 0;
  const x = (i % COLS) * w, y = Math.floor(i / COLS) * hgt;
  for (let line = 0; line < hgt; line++) atlas.set(rgba.subarray(line * w * 4, (line + 1) * w * 4), ((y + line) * w * COLS + x) * 4);
  const png = encodePNG(w, hgt, rgba), name = String(i).padStart(2, '0') + '.png';
  writeFileSync(join(folder, name), png);
  phaseHashes.push(SHA(rgba));
  rects.push([x, y, w, hgt]);
  frames.push({ filename: name, frame: { x, y, w, h: hgt }, rotated: false, trimmed: false,
    spriteSourceSize: { x: 0, y: 0, w, h: hgt }, sourceSize: { w, h: hgt }, duration: 1000 * TICKS / 60 });
}
const png = encodePNG(w * COLS, hgt * rows, atlas);
writeFileSync(join(folder, 'atlas.png'), png);
writeFileSync(join(folder, 'aseprite.json'), JSON.stringify({ frames, meta: {
  app: 'https://github.com/patch-gg/pixelfx', image: 'atlas.png', format: 'RGBA8888',
  size: { w: w * COLS, h: hgt * rows }, scale: '1',
  frameTags: [{ name: id, from: 0, to: COUNT - 1, direction: 'forward' }],
  pixelfx: { fps: 60 / TICKS, loop: true, columns: COLS, pivot: ANCHOR, frames: COUNT, frameSize: SIZE },
} }, null, 2) + '\n');

const catalog = { [id]: {
  id, texture: `res://assets/effects/ultraseven/${id}/atlas.png`, rects, anchor: ANCHOR,
  ticks: TICKS, loop: true, visual_scale: 1, display_scale: [1, 1], full_frame: true,
  alpha_binary: true, color_parameter: false, emission_anchor: true, orientation: 'authored',
  source_kind: 'pixelfx_code_baked', license: 'MIT', upstream_commit: UPSTREAM,
  authoring_source: 'res://tools/rebuild/ultraseven/seven-beam-pixelfx-20261117/bake.mjs',
  runtime_review_pending: true, user_approved: false,
} };
writeFileSync(join(OUT, 'catalog-candidate.json'), JSON.stringify(catalog, null, 2) + '\n');
writeFileSync(join(OUT, 'bundle.json'), JSON.stringify({
  schema: 'ufeneo.pixelfx.bake.v1', art_source: 'code', route: 'PixelFX offline', seed: SEED,
  upstream_commit: UPSTREAM, source_sha256: SHA(readFileSync(SELF)),
  license_sha256: SHA(readFileSync(join(ROOT, 'third_party/pixelfx/LICENSE'))),
  length: LENGTH, canvas: SIZE, anchor: ANCHOR,
  upstream: 'https://github.com/patch-gg/pixelfx/tree/' + UPSTREAM,
  exports: [{ id, phases: COUNT, ticks: TICKS, phase_rgba_sha256: phaseHashes, atlas_sha256: SHA(png) }],
}, null, 2) + '\n');
console.log(JSON.stringify({ output: OUT, exports: [{ id, phases: COUNT }] }));