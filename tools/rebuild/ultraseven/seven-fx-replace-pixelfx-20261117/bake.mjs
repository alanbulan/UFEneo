// 赛文替换批：宽幅扇束两档、光束命中/防御碎爆、可旋转头镖。
// PixelFX 离线烘焙，原生 1:1；不画正圆、同心环与等距射线，轮廓逐列扰动。
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
// 宽幅束沿用已批的暖白/金色档；命中碎爆用青白；头镖用银灰与本人红色根点。
const WIDE = fit(['#6b3410', '#a85718', '#d98a25', '#f6c24a', '#ffe485', '#fdf1bd', '#fffdf1', '#ffffff'], 8);
const BEAM = fit(['#102c5e', '#1c5489', '#267da8', '#45b6d9', '#83e1ef', '#c2f5ff', '#edfeff', '#ffffff'], 8);
const SILVER = fit(['#0e1218', '#343944', '#6e7280', '#a9adb8', '#d9dce4', '#f4f6fa', '#ffffff'], 7);
// 三级必杀起手：沿用赛文额灯的绿，不画同心环。
const GREEN = fit(['#0c2b1a', '#14512f', '#1d7a45', '#2fa862', '#63d98e', '#a7f4c0', '#dcffe8', '#ffffff'], 8);
const GLINT = '#c41f30';

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

// 宽幅扇：从根部向右张开。慢频定粗细，快频只咬边缘；亮结与细丝都不按等距排队。
function fan(p, phase, spec) {
  for (let x = 0; x < spec.span; x++) {
    const t = x / (spec.span - 1);
    const base = spec.root + (spec.tip - spec.root) * Math.pow(t, 0.72);
    const slow = noise(x / 47 + phase * 1.3, 311) - 0.5;
    const wob = noise(x / 11 + phase * 2.1, 977) - 0.5;
    // 连续起伏，不按阈值整列跳变，避免看起来像竖条台阶。
    const swell = Math.max(0, noise(x / 31 + phase * 0.8, 733) - 0.58) * 1.1;
    const half = Math.max(1, Math.round(base * (0.78 + slow * 0.34 + swell)));
    const top = Math.max(1, Math.round(half + wob * 2.2));
    const bot = Math.max(1, Math.round(half - wob * 1.8));
    for (let y = -top; y <= bot; y++) {
      const q = Math.abs(y) / (y < 0 ? top : bot);
      let level = q < 0.1 ? 7 : q < 0.26 ? 6 : q < 0.48 ? 5 : q < 0.72 ? 4 : q < 0.88 ? 3 : 2;
      // 两条不同周期的漂移峰，峰位随相移动，不排成等距脉冲。
      const knot = Math.max(
        1 - Math.abs(((x / (spec.span / 3.1) - phase * 1.17) % 1 + 1) % 1 - 0.5) * 2.6,
        1 - Math.abs(((x / (spec.span / 5.7) + 0.37 - phase * 0.83) % 1 + 1) % 1 - 0.5) * 2.6,
      );
      if (knot > 0.72) level = Math.min(7, level + 1);
      // 边缘随机缺口，避免平直上下边；只在最外一圈咬。
      if (q > 0.9 && h(x * 17 + y * 13 + phase * 7, 419) > 0.55) continue;
      p.dot(x, y, spec.pal[level]);
    }
    // 束身内部的暗色裂线，把整片亮面拆成几股。
    if (half > 4) {
      const c1 = Math.round((h(x * 7 + phase * 31, 83) - 0.5) * half * 1.5);
      const c2 = Math.round((h(x * 11 + phase * 47, 89) - 0.5) * half * 1.7);
      if (h(x * 3 + phase * 13, 97) > 0.62) p.dot(x, c1, spec.pal[2]);
      if (h(x * 5 + phase * 23, 101) > 0.7) p.dot(x, c2, spec.pal[3]);
    }
    // 内侧两条流线：位置逐相漂移，亮度比束身高一档。
    if (half > 3) {
      const f1 = Math.round((h(x * 7 + phase * 31, 113) - 0.5) * half * 1.1);
      const f2 = Math.round((h(x * 11 + phase * 47, 127) - 0.5) * half * 1.4);
      if (h(x * 3 + phase * 13, 131) > 0.42) p.dot(x, f1, spec.pal[7]);
      if (h(x * 5 + phase * 23, 137) > 0.62) p.dot(x, f2, spec.pal[6]);
    }
    // 偶尔甩出一两颗碎屑，位置不排直线。
    if (h(x * 19 + phase * 29, 103) > 0.86) p.dot(x, -top - 1, spec.pal[3]);
    if (h(x * 23 + phase * 37, 107) > 0.88) p.dot(x, bot + 1, spec.pal[2]);
  }
}

// 光束命中：不规则碎核 + 长短不一的碎刃 + 散点，逐相收缩；不画圆和同心环。
function burst(p, phase, spec) {
  const n = spec.count - 1, t = phase / n;
  const core = spec.core * Math.pow(1 - t, 0.5) + 1;
  const m = 9 + Math.floor(h(phase, 7) * 4);
  const pts = [];
  for (let i = 0; i < m; i++) {
    const a = (i / m) * TAU + (h(i + phase * 13, 9) - 0.5) * 0.8;
    const rr = core * (0.5 + h(i + phase * 17, 13) * 0.95);
    pts.push([Math.cos(a) * rr, Math.sin(a) * rr]);
  }
  // 深蓝描边压一层，青核才不会在命中白闪里糊掉；核内亮块仍不规则。
  p.poly(pts.map(([x, y]) => [x * 1.08 + 0.5, y * 1.08 + 0.5]), spec.pal[0], 1);
  p.poly(pts, spec.pal[4], 1);
  for (let k = 0; k < 12; k++) {
    const a = h(k + phase * 29, 17) * TAU, r = core * h(k, 19) * 0.55;
    p.dot(Math.cos(a) * r, Math.sin(a) * r, k % 3 ? spec.pal[6] : spec.pal[7]);
    if (k % 4 === 0) p.dot(Math.cos(a) * r + 1, Math.sin(a) * r, spec.pal[5]);
  }
  // 碎刃：前几相画成 2–3 像素的斜线，后面退成单像素余火。
  for (let k = 0; k < spec.shards; k++) {
    const born = h(k, 23) * n * 0.7;
    const age = phase - born;
    if (age <= 0) continue;
    const life = 8 + h(k, 29) * 8;
    if (age > life) continue;
    const a = (h(k, 31) - 0.5) * spec.spread - 0.15;
    const speed = spec.reach * (0.35 + h(k, 37) * 0.8);
    const x = Math.cos(a) * speed * (0.25 + age * 0.22);
    const y = Math.sin(a) * speed * (0.25 + age * 0.22);
    const k2 = Math.max(0, 1 - age / life);
    if (age < 4) {
      p.dot(x, y, spec.pal[6], k2);
      p.dot(x + Math.cos(a) * 1.7, y + Math.sin(a) * 1.7, spec.pal[4], k2);
      if (h(k, 41) > 0.4) p.dot(x + Math.cos(a) * 3.0, y + Math.sin(a) * 3.0, spec.pal[3], k2 * 0.9);
    } else {
      p.dot(x, y, spec.pal[3], k2 * 0.9);
      if (k2 > 0.5 && h(k, 41) > 0.5) p.dot(x + 1, y, spec.pal[2], k2 * 0.7);
    }
  }
  // 末相仍留少量余火，不出现整帧空白。
  if (t > 0.5) {
    for (let k = 0; k < 9; k++) {
      const a = h(k + 91, 43) * TAU;
      const r = core * (0.9 + h(k, 47) * 1.1);
      if (h(k, 53) > t * 0.45) p.dot(Math.cos(a) * r, Math.sin(a) * r, k % 2 ? spec.pal[4] : spec.pal[3]);
    }
  }
}

// 防御：压扁的不规则碎核 + 沿防御面向两侧弹开的短刃，没有同心弧。
function guard(p, phase, spec) {
  const n = spec.count - 1, t = phase / n;
  const core = spec.core * Math.pow(1 - t, 0.5) + 1;
  if (t < 0.8) {
    const m = 8 + Math.floor(h(phase, 23) * 3);
    const pts = [];
    for (let i = 0; i < m; i++) {
      const a = (i / m) * TAU + (h(i + phase * 11, 27) - 0.5) * 0.8;
      const rr = core * (0.55 + h(i + phase * 13, 29) * 0.8);
      pts.push([Math.cos(a) * rr * 1.25, Math.sin(a) * rr * 0.62]);
    }
    p.poly(pts.map(([x, y]) => [x * 1.08, y * 1.08]), spec.pal[0], 1);
    p.poly(pts, spec.pal[4], 1);
    for (let k = 0; k < 8; k++) {
      const a = h(k + phase * 31, 33) * TAU, r = core * h(k, 37) * 0.55;
      p.dot(Math.cos(a) * r * 1.2, Math.sin(a) * r * 0.6, k % 2 ? spec.pal[6] : spec.pal[7]);
    }
  }
  for (let k = 0; k < spec.shards; k++) {
    const born = h(k, 61) * n * 0.55, age = phase - born;
    if (age <= 0 || age > 8) continue;
    const a = (k % 2 ? 0 : Math.PI) + (h(k, 67) - 0.5) * 1.1;
    const r = 3 + age * spec.reach * 0.1;
    const x = Math.cos(a) * r, y = Math.sin(a) * r * 0.55;
    p.dot(x, y, age < 2 ? spec.pal[5] : spec.pal[3], Math.max(0, 1 - age / 8));
    if (age < 3) p.dot(x - Math.cos(a), y - Math.sin(a) * 0.5, spec.pal[2], 0.8);
  }
}

// 蓄气起手：三段不同半径的短弧绕前臂打转，弧长、相位、半径都逐相变化；不留完整圆。
function swirl(p, phase, spec) {
  const turn = phase / spec.count * TAU * 0.55;
  for (let ring = 0; ring < 3; ring++) {
    const baseR = spec.radius * (0.5 + ring * 0.3);
    for (let k = 0; k < spec.arcs; k++) {
      const a0 = h(k * 7 + ring * 13 + phase, 21) * TAU + turn * (ring % 2 ? 1 : -1);
      const len = Math.round(spec.arc * (0.55 + h(k + ring * 5, 23) * 0.9));
      for (let step = 0; step < len; step++) {
        const a = a0 + step * 0.17;
        const r = baseR + (h(k * 31 + step + phase * 7, 27) - 0.5) * 4;
        p.dot(Math.cos(a) * r, Math.sin(a) * r, step % 4 ? spec.pal[4] : spec.pal[5]);
        if (h(k * 37 + step + phase * 11, 29) > 0.72) {
          p.dot(Math.cos(a) * (r + 1), Math.sin(a) * (r + 1), spec.pal[3]);
        }
      }
    }
  }
  for (let k = 0; k < 10; k++) {
    const a = h(k + phase * 19, 31) * TAU;
    const r = spec.radius * (1.1 + h(k, 33) * 0.7);
    p.dot(Math.cos(a) * r, Math.sin(a) * r, h(k, 39) > 0.5 ? spec.pal[5] : spec.pal[3]);
  }
}

// 炮口起手：金色碎光向一侧炸开，长短与角度都不等距，没有整齐的直射线。
function muzzle(p, phase, spec) {
  const core = 9 - phase * 1.6;
  const m = 9 + Math.floor(h(phase, 3) * 3);
  const pts = [];
  for (let i = 0; i < m; i++) {
    const a = (i / m) * TAU + (h(i + phase * 7, 5) - 0.5) * 0.9;
    const rr = core * (0.6 + h(i + phase * 11, 7) * 0.9);
    pts.push([Math.cos(a) * rr, Math.sin(a) * rr]);
  }
  p.poly(pts, spec.pal[6], 1);
  for (let i = 0; i < 18; i++) {
    const a = (h(i, 13) - 0.5) * 2.2 - 0.1;
    const reach = spec.reach * (0.25 + h(i, 17) * 0.85) * (1 - phase * 0.12);
    const w = Math.round((1 - phase * 0.15) * (h(i, 19) > 0.6 ? 2 : 1));
    const r0 = 2 + h(i, 23) * 3;
    for (let r = r0; r < reach; r += 1) {
      const x = Math.cos(a) * r, y = Math.sin(a) * r * 0.8;
      p.dot(x, y, r < reach * 0.45 ? spec.pal[7] : spec.pal[4]);
      if (w > 1) p.dot(x, y + 1, spec.pal[5]);
    }
    if (h(i, 29) > 0.55) p.dot(Math.cos(a) * (reach + 2), Math.sin(a) * (reach + 2) * 0.8, spec.pal[3]);
  }
}

// 头镖：官方月牙刃。尖端收细，刃口朝前，按相旋转；根部一枚本人红色点。
function crescent(p, phase, spec) {
  const th = [0, 1.05, Math.PI / 2, -1.0][phase % 4];
  const R = 21, width = 6.5, steps = 26;
  const a0 = -Math.PI * 0.52, a1 = Math.PI * 0.52;
  const outer = [], inner = [];
  for (let i = 0; i <= steps; i++) {
    const a = a0 + (a1 - a0) * i / steps;
    const ro = R * (1 + (h(i + phase * 7, 17) - 0.5) * 0.05);
    const ri = ro - width * Math.sin((Math.PI * i) / steps);
    outer.push([Math.cos(a) * ro, Math.sin(a) * ro]);
    inner.push([Math.cos(a) * ri, Math.sin(a) * ri]);
  }
  const rot = ([x, y]) => [x * Math.cos(th) - y * Math.sin(th), x * Math.sin(th) + y * Math.cos(th)];
  const shape = outer.concat(inner.reverse()).map(rot);
  // 深色描边外扩一格，再压银色刃身。
  p.poly(shape.map(([x, y]) => [x * 1.05, y * 1.05]), SILVER[1], 1);
  p.poly(shape, SILVER[4], 1);
  // 外弧刃口高光。
  for (let i = 0; i <= steps * 0.72; i++) {
    const a = a0 + (a1 - a0) * i / steps;
    const [x, y] = rot([Math.cos(a) * (R - 0.4), Math.sin(a) * (R - 0.4)]);
    p.dot(x, y, SILVER[6]);
  }
  // 内侧一道灰影，读出手工开刃。
  for (let i = 3; i <= steps * 0.8; i++) {
    const a = a0 + (a1 - a0) * i / steps;
    const ri = R - width * Math.sin((Math.PI * i) / steps) + 0.9;
    const [x, y] = rot([Math.cos(a) * ri, Math.sin(a) * ri]);
    p.dot(x, y, SILVER[2]);
  }
  const [gx, gy] = rot([-R * 0.5, 0]);
  p.dot(gx, gy, GLINT);
  p.dot(gx + Math.cos(th), gy + Math.sin(th), GLINT);
}

const specs = [
  { id: 'seven_fx_wide1', size: [448, 128], anchor: [0, 64], count: 4, ticks: 4, draw: fan,
    params: { span: 448, root: 10, tip: 52, pal: WIDE } },
  { id: 'seven_fx_wide2', size: [560, 240], anchor: [0, 120], count: 4, ticks: 4, draw: fan,
    params: { span: 560, root: 16, tip: 104, pal: WIDE } },
  { id: 'seven_fx_emerium_start', size: [112, 96], anchor: [32, 32], count: 4, ticks: 4, draw: swirl,
    params: { radius: 20, arcs: 4, arc: 22, pal: GREEN } },
  { id: 'seven_fx_wide_start', size: [112, 96], anchor: [2, 48], count: 4, ticks: 4, draw: muzzle,
    params: { reach: 34, pal: WIDE } },
  { id: 'seven_pixelfx_emerium_hit', size: [112, 96], anchor: [56, 48], count: 19, ticks: 1, draw: burst,
    params: { core: 18, reach: 36, shards: 16, spread: 2.8, pal: BEAM } },
  { id: 'seven_pixelfx_emerium_guard', size: [96, 80], anchor: [48, 40], count: 15, ticks: 1, draw: guard,
    params: { core: 9, reach: 28, shards: 13, pal: BEAM } },
  { id: 'seven_slugger', size: [48, 48], anchor: [24, 24], count: 4, ticks: 3, draw: crescent,
    params: {} },
];

const catalog = {}, exports = [];
for (const spec of specs) {
  const [w, hgt] = spec.size, cols = 4, rows = Math.ceil(spec.count / cols);
  const atlas = new Uint8ClampedArray(w * cols * hgt * rows * 4);
  const folder = join(OUT, spec.id);
  mkdirSync(folder, { recursive: true });
  const rects = [], frames = [], phaseHashes = [];
  for (let i = 0; i < spec.count; i++) {
    const frame = createFrame(w, hgt);
    const p = painterFor(frame).place(...spec.anchor);
    spec.draw(p, i, { ...spec.params, count: spec.count });
    const rgba = composite(frame, new Uint8ClampedArray(w * hgt * 4), null);
    for (let q = 0; q < rgba.length; q += 4) if (rgba[q + 3] < 24) rgba.fill(0, q, q + 4);
    for (let q = 3; q < rgba.length; q += 4) rgba[q] = rgba[q] >= 128 ? 255 : 0;
    const x = (i % cols) * w, y = Math.floor(i / cols) * hgt;
    for (let line = 0; line < hgt; line++) atlas.set(rgba.subarray(line * w * 4, (line + 1) * w * 4), ((y + line) * w * cols + x) * 4);
    const png = encodePNG(w, hgt, rgba), name = String(i).padStart(2, '0') + '.png';
    writeFileSync(join(folder, name), png);
    phaseHashes.push(SHA(rgba));
    rects.push([x, y, w, hgt]);
    frames.push({ filename: name, frame: { x, y, w, h: hgt }, rotated: false, trimmed: false,
      spriteSourceSize: { x: 0, y: 0, w, h: hgt }, sourceSize: { w, h: hgt }, duration: 1000 * spec.ticks / 60 });
  }
  const png = encodePNG(w * cols, hgt * rows, atlas);
  writeFileSync(join(folder, 'atlas.png'), png);
  writeFileSync(join(folder, 'aseprite.json'), JSON.stringify({ frames, meta: {
    app: 'https://github.com/patch-gg/pixelfx', image: 'atlas.png', format: 'RGBA8888',
    size: { w: w * cols, h: hgt * rows }, scale: '1',
    frameTags: [{ name: spec.id, from: 0, to: spec.count - 1, direction: 'forward' }],
    pixelfx: { fps: 60 / spec.ticks, loop: spec.id === 'seven_fx_wide1' || spec.id === 'seven_fx_wide2', columns: cols, pivot: spec.anchor, frames: spec.count, frameSize: spec.size },
  } }, null, 2) + '\n');
  const created = new Date().toISOString().slice(0, 10);
  catalog[spec.id] = {
    id: spec.id,
    texture: `res://assets/effects/ultraseven/${spec.id}/atlas.png`,
    rects, anchor: spec.anchor, ticks: spec.ticks,
    loop: spec.id === 'seven_fx_wide1' || spec.id === 'seven_fx_wide2',
    visual_scale: 1, display_scale: [1, 1],
    alpha_binary: true, color_parameter: true,
    source_kind: 'pixelfx_code_baked', license: 'MIT', upstream_commit: UPSTREAM,
    authoring_source: 'res://tools/rebuild/ultraseven/seven-fx-replace-pixelfx-20261117/bake.mjs',
    runtime_review_pending: true, user_approved: false, review_status: `${created} 换相，待实机审`,
  };
  if (spec.id === 'seven_pixelfx_emerium_hit' || spec.id === 'seven_pixelfx_emerium_guard') {
    catalog[spec.id].emission_anchor = true;
  }
  if (spec.id === 'seven_fx_emerium_start') {
    catalog[spec.id].authoring_source = 'res://tools/rebuild/ultraseven/seven-fx-replace-pixelfx-20261117/bake.mjs';
  }
  if (spec.id === 'seven_fx_wide1') {
    catalog[spec.id].native_fan = true;
    catalog[spec.id].emission_surface_x = 2;
    catalog[spec.id].geometry_note = '整条原生宽幅扇形，单张显示，不裁中段、不平铺；边缘逐列扰动';
  }
  if (spec.id === 'seven_fx_wide2') {
    catalog[spec.id].native_fan = true;
    catalog[spec.id].emission_surface_x = 4;
    catalog[spec.id].geometry_note = '整条原生宽幅扇形，单张显示，不裁中段、不平铺；边缘逐列扰动';
  }
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