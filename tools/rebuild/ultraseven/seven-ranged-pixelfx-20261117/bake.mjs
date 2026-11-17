// 赛文两支近身感远程招的专属飞行物：楔形光线（掌刃）与超级念力。
// PixelFX 离线烘焙，原生 1:1 整帧，游戏只播放透明图集。
// 画法：不等距、不正圆、不画同心环；轮廓由逐列扰动咬出参差边缘。
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
// 楔刃沿用青白档，和艾梅利姆同一族。
const BLADE = fit(['#0f274f', '#1b4a7d', '#256f9c', '#3fa6c4', '#78d8e6', '#bdf2f8', '#ecfeff', '#ffffff'], 8);
// 念力用赛文的绿：暗墨绿到亮青白，和蓝色光束一眼分开。
const PSI = fit(['#0c2b1a', '#14512f', '#1d7a45', '#2fa862', '#63d98e', '#a7f4c0', '#dcffe8', '#ffffff'], 8);

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

// 楔形掌刃：刀身略上扬，根部厚、刀口收成两像素；后缘按列咬出缺口，不画等距条纹。
function wedgeBlade(p, phase, spec) {
  for (let x = 0; x <= spec.span; x++) {
    const t = x / spec.span;
    const cy = -2.2 * t + (noise(x / 13 + phase * 0.7, 907) - 0.5) * 2.4;
    const peak = 2 + 8.5 * Math.pow(1 - t, 1.25);
    const wob = noise(x / 5.5 + phase * 1.1, 311) - 0.5;
    const up = Math.max(1, peak * (0.95 + wob * 0.85));
    const lo = Math.max(1, peak * (0.42 + wob * 0.75));
    const y0 = Math.round(cy - up), y1 = Math.round(cy + lo);
    for (let y = y0; y <= y1; y++) {
      const q = Math.abs((y - cy) / (y < cy ? up : lo));
      // 后缘撕裂：上缘随机缺一两种像素，避免整齐的平口。
      if (t < 0.24 && y <= y0 + 1 && h(x * 19 + y * 7, 83) > 0.72) continue;
      const level = q < 0.3 ? 7 : q < 0.55 ? 6 : q < 0.8 ? 5 : q < 0.95 ? 4 : 3;
      p.dot(x, y, BLADE[level]);
    }
    if (t < 0.55 && h(x * 13 + phase * 7, 71) > 0.72) {
      p.dot(x, y0 - 1, BLADE[2]);
      if (h(x * 17 + phase * 3, 73) > 0.5) p.dot(x, y1 + 1, BLADE[2]);
    }
    // 刀口高光只落在最后一段。
    if (t > 0.7 && h(x * 7 + phase * 53, 79) > 0.4) p.dot(x, Math.round(cy - up) + 1, BLADE[7]);
  }
  // 拖尾碎屑向后上方散，越晚越暗。
  for (let k = 0; k < spec.shards; k++) {
    const age = Math.max(0, phase - h(k, 23) * 0.6);
    const x = -3 - h(k, 29) * 10 - age * 2.5;
    const y = (h(k, 31) - 0.5) * 16 - age * 1.6;
    p.dot(x, y, age > 1.2 ? BLADE[3] : BLADE[5]);
    if (h(k, 37) > 0.6) p.dot(x - 1, y + 1, BLADE[2]);
  }
}

// 念力：不画同心环。三到四条长短不一的锯齿臂绕偏心核扭动，臂身逐像素连成线。
function psychic(p, phase, spec) {
  const spin = phase / spec.count * TAU * 0.9;
  const coreX = (h(phase, 13) - 0.5) * 6, coreY = (h(phase, 17) - 0.5) * 6;
  for (let i = 0; i < 30; i++) {
    const a = h(i, 41) * TAU, r = 4 + h(i, 43) * 8;
    p.dot(coreX + Math.cos(a) * r, coreY + Math.sin(a) * r * 0.8, i % 5 ? PSI[5] : PSI[6]);
  }
  p.dot(coreX, coreY, PSI[7]); p.dot(coreX + 1, coreY, PSI[7]); p.dot(coreX, coreY + 1, PSI[7]);
  for (let arm = 0; arm < spec.arms; arm++) {
    const base = arm / spec.arms * TAU + spin * (arm % 2 ? -1 : 1);
    const length = spec.reach * (0.5 + h(arm, 53) * 0.6);
    let x = coreX + Math.cos(base) * 6, y = coreY + Math.sin(base) * 6;
    for (let step = 0; step < Math.round(length); step++) {
      const a = base + (h(arm * 41 + Math.floor(step / 3), 59) - 0.5) * 0.85;
      x += Math.cos(a); y += Math.sin(a) * 0.9;
      p.dot(x, y, step < 6 ? PSI[6] : PSI[4]);
      if (step < 10) p.dot(x + 1, y, PSI[3]);
      if (step % 4 === 0 && h(step + arm * 7, 61) > 0.5) p.dot(x, y + 1, PSI[3]);
    }
  }
  for (let k = 0; k < spec.shards; k++) {
    const a = h(k * 7 + phase, 67) * TAU;
    const r = spec.reach * (0.6 + h(k, 71) * 0.45);
    p.dot(coreX + Math.cos(a) * r, coreY + Math.sin(a) * r * 0.85,
      h(k, 73) > 0.6 ? PSI[6] : PSI[3]);
  }
}

const specs = [
  { id: 'seven_wedge_core', size: [96, 64], anchor: [20, 32], count: 4, ticks: 4, draw: wedgeBlade,
    params: { span: 42, shards: 9 } },
  { id: 'seven_psychic_core', size: [112, 112], anchor: [56, 56], count: 4, ticks: 4, draw: psychic,
    params: { arms: 4, reach: 38, shards: 14 } },
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
    pixelfx: { fps: 60 / spec.ticks, loop: true, columns: cols, pivot: spec.anchor, frames: spec.count, frameSize: spec.size },
  } }, null, 2) + '\n');
  catalog[spec.id] = {
    id: spec.id, texture: `res://assets/effects/ultraseven/${spec.id}/atlas.png`,
    rects, anchor: spec.anchor, ticks: spec.ticks, loop: true, visual_scale: 1, display_scale: [1, 1],
    alpha_binary: true, color_parameter: false, source_kind: 'pixelfx_code_baked', license: 'MIT',
    upstream_commit: UPSTREAM, orientation: 'authored',
    authoring_source: 'res://tools/rebuild/ultraseven/seven-ranged-pixelfx-20261117/bake.mjs',
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