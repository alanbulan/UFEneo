// 赛文普通拳脚专属火光：PixelFX 离线烘焙，游戏只播放透明整帧。
// 只画火花与碎裂，不画人物、不画招式特效；色板取本人红银，与共享星芒区分。
// MIT License, Copyright (c) 2026 Patch and Hugo Duprez. See third_party/pixelfx/LICENSE.
import { createFrame, painterFor, composite, fit, TAU } from '../../../../third_party/pixelfx/src/core/index.js';
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

// 七色暖档：暗红→砖红→朱红→橙→金→浅金→奶白→纯白。红银配色，不用共享星芒的黄蓝。
const HEAT = fit(['#5c1119', '#8e1626', '#c41f30', '#e8501f', '#ff9314', '#ffd148', '#fff0bd', '#ffffff'], 8);
// 防御档：银白偏青，和命中档一眼分开。
const GUARD = fit(['#123642', '#1a5a6b', '#25869a', '#3fb9cc', '#7fe0ea', '#c8f6ff', '#efffff', '#ffffff'], 8);

function h(k, salt) {
  let n = (k * 2654435761 + salt * 40503 + SEED) >>> 0;
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}

// 手绘冲击：没有正圆、没有等距射线、没有同心环。
// 白核是不规则碎块，四周是长短不一、带折角的碎刃，再散几粒火星。
function blob(p, r, c, k = 1, seed = 0, jitter = 0.5) {
  const pts = [], n = 6 + Math.floor(h(seed, 7) * 4);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * TAU + (h(i + seed * 13, 9) - 0.5) * 0.62;
    const rr = r * (1 - jitter * 0.5 + jitter * h(i + seed * 17, 13));
    pts.push([Math.cos(a) * rr, Math.sin(a) * rr]);
  }
  p.poly(pts, c, k);
}

// 折角碎刃：根部有宽度，中段偏一点，尖端错开，读起来是崩开的碎片而不是箭头。
function shard(p, a, r0, r1, w, c, k = 1, bend = 0) {
  const ax = Math.cos(a), ay = Math.sin(a), nx = -ay, ny = ax;
  if (r1 <= r0 + 1) return;
  const mx = (r0 + r1) * 0.55, bx = nx * bend, by = ny * bend;
  p.poly([
    [ax * r0 - nx * w, ay * r0 - ny * w],
    [ax * r0 + nx * w, ay * r0 + ny * w],
    [ax * mx + nx * w * 0.55 + bx, ay * mx + ny * w * 0.55 + by],
    [ax * r1 + bx * 1.8 + nx * 0.5, ay * r1 + by * 1.8 + ny * 0.5],
  ], c, k);
}

function heat(p, phase, spec) {
  const n = spec.count - 1;
  const fade = spec.fade[Math.min(phase, spec.fade.length - 1)];
  const grow = spec.grow[Math.min(phase, spec.grow.length - 1)];
  const core = spec.core * spec.coreScale[Math.min(phase, spec.coreScale.length - 1)];
  // 白核：不规则块，第二、三帧偏两像素，让闪点每帧位置都不一样。
  if (core >= 1.2) {
    const jx = (h(phase, 91) - 0.5) * core * 0.5, jy = (h(phase, 93) - 0.5) * core * 0.5;
    blob(p, core * 1.15, phase <= 1 ? HEAT[6] : HEAT[5], fade, phase + 1, 0.7);
    blob(p, core * 0.72, HEAT[7], 1, phase + 5, 0.45);
    if (core > 3) p.dot(jx, jy, HEAT[7], 1);
  }
  // 碎刃：角度成簇、长短差得开，朝攻击方向的那几片最长。
  for (let k = 0; k < spec.rays; k++) {
    const cluster = h(k, 11) < 0.72 ? 0.55 : 1.15;
    const a = (h(k, 11) - 0.5) * spec.spread * cluster - 0.12;
    const reach = spec.reach * grow * (0.42 + 0.72 * h(k, 23)) * (k % 3 === 0 ? 1.12 : 0.86);
    const roll = h(k, 29);
    const r0 = core * 0.7 + 0.5;
    const w = Math.max(1, Math.round(spec.width * (roll > 0.6 ? 1 : 0.6)));
    const color = roll > 0.66 ? HEAT[5] : roll > 0.3 ? HEAT[4] : HEAT[3];
    shard(p, a, r0, reach, w, color, fade, (h(k, 47) - 0.5) * 2.4);
  }
  // 火星：单像素与两像素点混着撒，位置不按角度均分。
  for (let k = 0; k < spec.shards; k++) {
    const born = h(k, 31) * (n - 1) * 0.8;
    const age = phase - born;
    if (age <= 0) continue;
    const life = 1.1 + h(k, 37) * 1.8;
    if (age > life) continue;
    const a = (h(k, 41) - 0.5) * spec.spread * 1.45 - 0.2;
    const speed = spec.reach * (0.35 + h(k, 43) * 0.8);
    const x = Math.cos(a) * speed * (0.45 + age * 0.55) + (h(k, 51) - 0.5) * 2;
    const y = Math.sin(a) * speed * (0.45 + age * 0.55) + age * age * 0.7;
    const k2 = 1 - age / life;
    p.dot(x, y, age < 1 ? HEAT[6] : HEAT[4], k2);
    if (k2 > 0.55 && h(k, 57) > 0.45) p.dot(x + (h(k, 59) > 0.5 ? 1 : -1), y, HEAT[3], k2 * 0.8);
  }
}

// 防御：贴着防御面擦出的一串短斜线，两头长中间短，再撒几粒青白火星。
function guard(p, phase, spec) {
  const n = spec.count - 1;
  const fade = 1 - phase / n;
  if (phase <= spec.flash) {
    blob(p, spec.core * 1.1, GUARD[6], fade, phase + 2, 0.6);
    blob(p, spec.core * 0.6, GUARD[7], 1, phase + 6, 0.4);
  }
  for (let k = 0; k < spec.rays; k++) {
    const born = h(k, 57) * (n - 1) * 0.55;
    const age = phase - born;
    if (age <= 0 || age > 2.6) continue;
    const a = (h(k, 61) - 0.5) * 2.0;
    const reach = spec.reach * (0.4 + 0.7 * h(k, 63)) * Math.min(1, 0.5 + age * 0.6);
    const start = spec.core * 0.5 + 1 + age * 2;
    shard(p, a, start, Math.max(start + 2, reach), 1, age < 1 ? GUARD[5] : GUARD[3], 1 - age / 2.6, (h(k, 67) - 0.5) * 2);
  }
  for (let k = 0; k < spec.shards; k++) {
    const born = h(k, 71) * n * 0.6, age = phase - born;
    if (age <= 0 || age > 2.4) continue;
    const a = (h(k, 79) - 0.5) * 2.3;
    const x = Math.cos(a) * (spec.reach * (0.25 + h(k, 83) * 0.55)) * (0.4 + age * 0.6);
    const y = Math.sin(a) * (spec.reach * (0.25 + h(k, 83) * 0.55)) * (0.4 + age * 0.6) + age * age * 0.5;
    p.dot(x, y, age < 1 ? GUARD[6] : GUARD[4], Math.max(0, 1 - age / 2.4));
  }
}

const specs = [
  { id: 'seven_hit_light', size: [56, 56], count: 5, ticks: [1, 2, 2, 1, 1], draw: heat,
    params: { core: 3.6, width: 1, glow: 11, ring: 0, reach: 22, rays: 7, spread: 1.6, shards: 5,
      grow: [0.42, 1, 0.9, 0.6, 0.28], fade: [0.85, 1, 0.9, 0.7, 0.45], coreScale: [0.8, 1, 0.75, 0.5, 0.35] } },
  { id: 'seven_hit_medium', size: [80, 80], count: 6, ticks: [1, 2, 2, 2, 1, 1], draw: heat,
    params: { core: 4.8, width: 2, glow: 16, ring: 24, reach: 32, rays: 9, spread: 1.7, shards: 8,
      grow: [0.45, 1, 0.95, 0.8, 0.5, 0.25], fade: [0.85, 1, 1, 0.85, 0.6, 0.4], coreScale: [0.8, 1, 0.85, 0.6, 0.45, 0.3] } },
  { id: 'seven_hit_heavy', size: [104, 104], count: 7, ticks: [1, 2, 2, 2, 2, 1, 1], draw: heat,
    params: { core: 6.2, width: 3, glow: 24, ring: 34, reach: 44, rays: 13, spread: 1.8, shards: 12,
      grow: [0.45, 1, 1, 0.9, 0.72, 0.45, 0.22], fade: [0.85, 1, 1, 0.95, 0.8, 0.55, 0.35],
      coreScale: [0.8, 1, 1, 0.85, 0.65, 0.45, 0.3] } },
  { id: 'seven_hit_guard', size: [64, 64], count: 5, ticks: [1, 2, 2, 1, 1], draw: guard,
    params: { core: 3.4, glow: 13, ring: 0, reach: 22, rays: 9, spread: 0, shards: 6, flash: 1 } },
];

const catalog = {}, exports = [];
for (const spec of specs) {
  const [w, hgt] = spec.size, cols = Math.min(4, spec.count), rows = Math.ceil(spec.count / cols);
  const anchor = [Math.floor(w / 2), Math.floor(hgt / 2)];
  const atlas = new Uint8ClampedArray(w * cols * hgt * rows * 4);
  const folder = join(OUT, spec.id);
  mkdirSync(folder, { recursive: true });
  const rects = [], frames = [], phaseHashes = [];
  let fps = 0;
  for (let i = 0; i < spec.count; i++) {
    const frame = createFrame(w, hgt);
    const p = painterFor(frame).place(...anchor);
    spec.draw(p, i, { ...spec.params, count: spec.count });
    const rgba = composite(frame, new Uint8ClampedArray(w * hgt * 4), null);
    // 三阶以下全透明：不留隐藏 RGB，也不给辉光门留下细碎噪点。
    for (let q = 0; q < rgba.length; q += 4) if (rgba[q + 3] < 24) rgba.fill(0, q, q + 4);
    for (let q = 3; q < rgba.length; q += 4) rgba[q] = rgba[q] >= 128 ? 255 : 0;
    const x = (i % cols) * w, y = Math.floor(i / cols) * hgt;
    for (let row = 0; row < hgt; row++) atlas.set(rgba.subarray(row * w * 4, (row + 1) * w * 4), ((y + row) * w * cols + x) * 4);
    const png = encodePNG(w, hgt, rgba), name = String(i).padStart(2, '0') + '.png';
    writeFileSync(join(folder, name), png);
    phaseHashes.push(SHA(rgba));
    rects.push([x, y, w, hgt]);
    fps += spec.ticks[i];
    frames.push({ filename: name, frame: { x, y, w, h: hgt }, rotated: false, trimmed: false,
      spriteSourceSize: { x: 0, y: 0, w, h: hgt }, sourceSize: { w, h: hgt }, duration: 1000 * spec.ticks[i] / 60 });
  }
  const png = encodePNG(w * cols, hgt * rows, atlas);
  writeFileSync(join(folder, 'atlas.png'), png);
  writeFileSync(join(folder, 'aseprite.json'), JSON.stringify({ frames, meta: {
    app: 'https://github.com/patch-gg/pixelfx', image: 'atlas.png', format: 'RGBA8888',
    size: { w: w * cols, h: hgt * rows }, scale: '1',
    frameTags: [{ name: spec.id, from: 0, to: spec.count - 1, direction: 'forward' }],
    pixelfx: { fps: 60 / Math.max(...spec.ticks), loop: false, columns: cols, pivot: anchor, frames: spec.count, frameSize: spec.size },
  } }, null, 2) + '\n');
  catalog[spec.id] = {
    id: spec.id, texture: `res://assets/effects/ultraseven/${spec.id}/atlas.png`,
    rects, anchor, ticks: spec.ticks, loop: false, visual_scale: 1, display_scale: [1, 1],
    alpha_binary: true, color_parameter: false, ordinary_melee_only: true, layer: 'hit',
    source_kind: 'pixelfx_code_baked', license: 'MIT', upstream_commit: UPSTREAM,
    authoring_source: 'res://tools/rebuild/ultraseven/seven-melee-pixelfx-20261117/bake.mjs',
    runtime_review_pending: true, user_approved: false,
  };
  exports.push({ id: spec.id, phases: spec.count, ticks: spec.ticks, phase_rgba_sha256: phaseHashes, atlas_sha256: SHA(png) });
}
writeFileSync(join(OUT, 'catalog-candidate.json'), JSON.stringify(catalog, null, 2) + '\n');
writeFileSync(join(OUT, 'bundle.json'), JSON.stringify({
  schema: 'ufeneo.pixelfx.bake.v1', art_source: 'code', route: 'PixelFX offline', seed: SEED,
  upstream_commit: UPSTREAM, source_sha256: SHA(readFileSync(SELF)),
  license_sha256: SHA(readFileSync(join(ROOT, 'third_party/pixelfx/LICENSE'))),
  upstream: 'https://github.com/patch-gg/pixelfx/tree/' + UPSTREAM, exports,
}, null, 2) + '\n');
console.log(JSON.stringify({ output: OUT, exports: exports.map(e => ({ id: e.id, phases: e.phases })) }));