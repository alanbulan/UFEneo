// 角色专属特效家族：PixelFX 离线烘焙原创像素形状（不沿用借用图集的轮廓）。
// PixelFX MIT, upstream a84159688af3ca37a4be05a0d422b94451b2e24e.
//
// 输入：stdin JSON
//   {character, families:[{name, out, kind, palette, seed, width, height, anchor,
//                          rects, frames:[{art:[x,y,w,h]}...]}]}
// 输出：--out 目录下每家族 atlas.png（按 rects 原坐标拼回）+ frame-N.png + bake.json
// 画法遵守 AGENTS：亮芯、外焰、颗粒、相位变化；硬 Alpha；形状全部由本文件的绘制函数生成。
import { createFrame, painterFor, composite } from '../../../third_party/pixelfx/src/core/fx.js';
import { fit, WHITE } from '../../../third_party/pixelfx/src/core/color.js';
import { TAU } from '../../../third_party/pixelfx/src/core/math.js';
import { encodePNG } from '../../../third_party/pixelfx/tools/lib/png.mjs';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const SELF = fileURLToPath(import.meta.url);
const ROOT = resolve(dirname(SELF), '../../..');
const arg = process.argv.indexOf('--out');
if (arg < 0) throw Error('需要 --out <输出目录>');
const OUT = resolve(ROOT, process.argv[arg + 1]);
if (!OUT.startsWith(ROOT + '/')) throw Error('输出必须在工程内');
const SHA = (b) => createHash('sha256').update(b).digest('hex');

// ---- 确定性噪声（同 seed 必得同像素）
function hash01(n, seed) {
  n = (n + Math.imul(seed | 0, 374761393)) >>> 0;
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}
function noise1(x, seed) {
  const k = Math.floor(x), u = x - k, f = u * u * (3 - 2 * u);
  return hash01(k, seed) * (1 - f) + hash01(k + 1, seed) * f;
}
const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);

// ---- 形状基元
function star(p, cx, cy, r, C, seed, spikes = 8) {
  for (let k = 0; k < spikes; k++) {
    const a = k * TAU / spikes + (hash01(k, seed) - 0.5) * 0.3;
    const len = r * (0.55 + 0.45 * hash01(k + 17, seed + 3));
    const steps = Math.max(2, Math.round(len));
    for (let t = 1; t <= steps; t++) {
      const u = t / steps;
      p.dot(cx + Math.cos(a) * len * u, cy + Math.sin(a) * len * u,
        u > 0.82 ? C[4] : k % 2 ? C[5] : C[6], u > 0.9 ? 0.55 : 1);
    }
  }
  p.circle(cx, cy, Math.max(1.4, r * 0.2), C[6], 1);
  p.circle(cx, cy, Math.max(1, r * 0.09), C[7], 1);
}

function raggedRing(p, cx, cy, r, C, seed, frame, level = 4, thick = 2) {
  const step = Math.max(0.014, 1.6 / Math.max(6, r));
  const phase = hash01(frame * 7 + 1, seed) * TAU;
  for (let a = phase; a < phase + TAU; a += step) {
    const dash = hash01(Math.floor((a - phase) * 97), seed + frame * 13);
    if (dash > 0.72) continue;
    for (let w = 0; w < thick; w++) {
      const rr = (r - w) * (0.94 + 0.1 * noise1(a * 3.1 + frame * 1.7, seed + 5));
      p.dot(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr, w === 0 ? C[level] : C[level - 1], w === 0 ? 1 : 0.7);
    }
    if (dash < 0.16) p.dot(cx + Math.cos(a) * (r + 1), cy + Math.sin(a) * (r + 1), C[level - 1], 0.5);
  }
}

// ---- 蓄力：向心聚能，亮核 + 旋转弧 + 十字耀斑 + 收束颗粒
function drawCharge(p, i, n, R, C, seed, oneshot) {
  // 循环蓄力做呼吸脉冲；一次性蓄力逐帧增强后收束。
  const seq = oneshot ? [0.28, 0.55, 0.82, 1.0][Math.min(i, 3)] : [0.72, 0.92, 1.0, 0.84][Math.min(i, 3)];
  const ph = (i / n) * TAU;
  // 外层断续光环
  raggedRing(p, 0, 0, R * (0.72 + 0.08 * Math.sin(ph)), C, seed, i, 3);
  // 三条旋转弧，方向每帧推进
  for (let s = 0; s < 3; s++) {
    const a0 = ph + s * TAU / 3;
    const span = 0.42 + 0.22 * hash01(s, seed + 11);
    const rad = R * (0.5 + 0.05 * Math.sin(ph + s * 1.4));
    const steps = Math.max(6, Math.round(rad * span * 2.4));
    for (let t = 0; t <= steps; t++) {
      const a = a0 + span * (t / steps);
      p.dot(Math.cos(a) * rad, Math.sin(a) * rad, t < steps * 0.4 ? C[6] : C[5], 0.95);
      p.dot(Math.cos(a) * (rad + 1.2), Math.sin(a) * (rad + 1.2), C[4], 0.5);
    }
  }
  // 八向辐条，隔帧转 22.5°
  const rot = (i % 2) * (Math.PI / 8);
  for (let s = 0; s < 8; s++) {
    const a = rot + s * TAU / 8;
    const r0 = R * 0.16;
    const r1 = R * (0.34 + 0.1 * seq + 0.03 * hash01(s, seed + 21));
    p.line(Math.cos(a) * r0, Math.sin(a) * r0, Math.cos(a) * r1, Math.sin(a) * r1,
      s % 2 ? C[6] : C[5], 0.9);
  }
  // 内层点状光晕，避免只剩细线
  const halo = R * (0.34 + 0.16 * seq);
  for (let k = 0; k < Math.round(halo * halo * 0.9); k++) {
    const a = hash01(k * 5 + 3, seed + 41) * TAU;
    const rad = halo * Math.sqrt(hash01(k * 7 + 5, seed + 43));
    p.dot(Math.cos(a) * rad, Math.sin(a) * rad, C[3 + (k % 2)], 0.22 + 0.3 * (1 - rad / halo));
  }
  // 亮核
  const rc = 1.8 + 3.6 * seq;
  p.circle(0, 0, rc, C[5], 1);
  p.circle(0, 0, rc * 0.62, C[6], 1);
  p.circle(0, 0, Math.max(1, rc * 0.26), C[7], 1);
  // 十字耀斑：根部加宽，尖端收细
  const fl = R * (0.45 + 0.4 * seq);
  for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
    for (let t = rc + 1; t < fl; t++) {
      const w = 2.6 * (1 - t / fl) ** 0.8;
      p.dot(dx * t, dy * t, C[6], 1);
      for (let d = 1; d <= Math.floor(w); d++) {
        p.dot(dx * t + dy * d, dy * t + dx * d, C[5], d <= w - 1 ? 0.95 : 0.6);
        p.dot(dx * t - dy * d, dy * t - dx * d, C[5], d <= w - 1 ? 0.95 : 0.6);
      }
    }
  }
  // 向心颗粒：逐帧收束，同时带切向漂移
  const count = Math.min(52, Math.max(14, Math.round(R * 1.5)));
  for (let k = 0; k < count; k++) {
    const a = hash01(k * 3 + 1, seed + 9) * TAU + i * 0.55;
    const base = 0.3 + 0.7 * hash01(k * 5 + 2, seed + 11);
    const shrink = oneshot ? 1 - 0.2 * i : 1 - 0.14 * i;
    const rad = R * (0.14 + 0.86 * base * clamp01(shrink));
    p.dot(Math.cos(a) * rad, Math.sin(a) * rad * 0.92,
      C[4 + (k % 2)], 0.55 + 0.4 * hash01(k + 7, seed + 31));
  }
}

// ---- 光束：亮芯 + 内焰 + 外焰 + 相位噪声 + 边缘光屑
function drawBeam(p, i, n, box, C, seed, fan) {
  const x0 = box.x, x1 = box.x + box.w - 1;
  const cy = box.y + box.h / 2;
  const H = box.h / 2;
  const total = Math.max(1, x1 - x0);
  for (let x = x0; x <= x1; x++) {
    const u = (x - x0) / total;
    const edge = Math.min(1, (x - x0 + 3) / 10, (x1 - x) / 12);
    const warp = noise1((x - i * 11) / 37, seed + 101);
    let rr = H * (0.5 + 0.13 * warp + 0.09 * noise1((x + i * 9) / 13, seed + 201));
    if (fan) rr *= 1 + 0.2 * Math.exp(-Math.max(0, x - x0) / 30);
    rr = Math.min(rr, H * 0.62);
    rr *= edge * (0.9 + 0.1 * Math.sin(u * Math.PI));
    if (rr < 0.55) {
      p.dot(x, cy, C[7], 0.8);
      continue;
    }
    const yTop = Math.ceil(rr * 1.75);
    for (let y = -yTop; y <= yTop; y++) {
      const q = Math.abs(y) / rr;
      if (q > 1.7) continue;
      const vein = noise1((x + i * 7 + y * 5) / 9, seed + 301);
      let lvl = q < 0.14 ? 7 : q < 0.32 ? 6 : q < 0.56 ? 5 : q < 0.82 ? 4 : q < 1.1 ? 3 : q < 1.4 ? 2 : 1;
      if (q > 0.24 && q < 0.78 && vein < 0.2) lvl = Math.max(2, lvl - 2);
      let a = q < 0.88 ? 1 : q < 1.16 ? 0.78 : q < 1.45 ? 0.46 : 0.24;
      if (q > 0.92 && noise1((x - i * 13) / 3.7, seed + 401) < 0.3) a *= 0.25;
      p.dot(x, cy + y, C[lvl], a * edge);
    }
    // 中央亮芯，束轴随相位轻微起伏
    if (rr > 1.2) {
      const wob = Math.round((noise1((x - i * 5) / 29, seed + 501) - 0.5) * Math.max(2, rr * 0.22));
      p.dot(x, cy + wob, C[7], 1);
      p.dot(x, cy + wob + 1, C[6], 0.78);
      p.dot(x, cy + wob - 1, C[6], 0.78);
    }
    // 贴边光屑（不脱离主体）
    if (x % 3 === 0) {
      const s = hash01(x * 7 + i, seed + 601);
      if (s < 0.2) {
        const side = s < 0.1 ? 1 : -1;
        const yy = cy + side * (rr + 1);
        const len = 2 + Math.floor(hash01(x + i * 13, seed + 701) * 5);
        p.line(x, yy, x + len, yy + side * 0.6, C[4], 0.8);
      }
    }
  }
  // 枪口/命中端耀斑
  const fr = Math.min(Math.max(6, H * 0.8), 20);
  star(p, x0, cy, fr, C, seed + 801, 8);
  if (x1 - x0 > 40) star(p, x1, cy, fr * 0.55, C, seed + 802, 6);
}

// ---- 弹体：分层椭圆 + 旋转尖刺，全部落在原脚位框内
function drawOrb(p, i, n, box, C, seed) {
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const rx = Math.max(2, box.w / 2 - 1), ry = Math.max(2, box.h / 2 - 1);
  p.ellipse(cx, cy, rx, ry, (d, ang) => {
    const rag = 0.88 + 0.12 * noise1(ang * 4 + i * 2, seed);
    if (d > rag) return 0;
    const q = d / rag;
    return q < 0.12 ? C[7] : q < 0.3 ? C[6] : q < 0.55 ? C[5] : q < 0.8 ? C[4] : C[3];
  }, 1);
  // 边缘抖动，让轮廓逐帧变化
  for (let k = 0; k < Math.round((rx + ry) * 1.5); k++) {
    const a = hash01(k, seed + 3) * TAU;
    const r = 0.9 + 0.16 * hash01(k + 9 + i * 5, seed + 5);
    p.dot(cx + Math.cos(a) * rx * r, cy + Math.sin(a) * ry * r, C[3], 0.5);
  }
  // 四向短刺，帧间旋转
  for (let s = 0; s < 4; s++) {
    const a = (i % 4) * 0.2 + s * TAU / 4;
    const tip = s % 2 ? 0.99 : 0.82;
    p.line(cx + Math.cos(a) * rx * 0.6, cy + Math.sin(a) * ry * 0.6,
      cx + Math.cos(a) * rx * tip, cy + Math.sin(a) * ry * tip, s % 2 ? C[5] : C[6], 0.9);
  }
  p.circle(cx, cy, Math.max(1.2, Math.min(rx, ry) * 0.38), C[6], 1);
  p.circle(cx, cy, Math.max(1, Math.min(rx, ry) * 0.16), C[7], 1);
}

// ---- 横长光弹：两端收尖的透镜形，中心亮芯贯穿
function drawBolt(p, i, n, box, C, seed) {
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const rx = Math.max(3, box.w / 2 - 1), ry = Math.max(2, box.h / 2 - 1);
  for (let x = -Math.ceil(rx); x <= Math.ceil(rx); x++) {
    const u = x / rx;
    if (Math.abs(u) > 1) continue;
    const taper = Math.pow(1 - Math.abs(u), 0.42);
    const rr = ry * taper * (0.72 + 0.28 * noise1((x + i * 6) / 7, seed + 11));
    if (rr < 0.5) continue;
    for (let y = -Math.ceil(rr); y <= Math.ceil(rr); y++) {
      const q = Math.abs(y) / rr;
      let lvl = q < 0.08 ? 7 : q < 0.22 ? 6 : q < 0.45 ? 5 : q < 0.72 ? 4 : q < 0.92 ? 3 : 2;
      // 内焰条纹：沿弹体相位流动，避免整块平涂
      if (q > 0.2 && q < 0.85) {
        const vein = noise1((x + i * 7 + y * 3) / 5.5, seed + 31);
        if (vein > 0.76) lvl = Math.min(7, lvl + 1);
        else if (vein < 0.2) lvl = Math.max(2, lvl - 1);
      }
      p.dot(cx + x, cy + y, C[lvl], q < 0.92 ? 1 : 0.55);
    }
  }
  for (let x = -Math.round(rx * 0.82); x <= Math.round(rx * 0.82); x++) {
    p.dot(cx + x, cy, C[7], 1);
    p.dot(cx + x, cy + 1, C[6], 0.5);
    p.dot(cx + x, cy - 1, C[6], 0.5);
  }
  // 上下外焰的相位起伏
  for (let k = 0; k < Math.round(rx * 0.9); k++) {
    const x = Math.round((hash01(k + i * 31, seed + 51) * 2 - 1) * rx * 0.9);
    const side = k % 2 ? 1 : -1;
    const yy = Math.round(ry * Math.pow(1 - Math.abs(x / rx), 0.5) + 1 + hash01(k, seed + 61) * 2);
    p.dot(cx + x, cy + side * yy, C[3], 0.55);
  }
  // 尾部三缕拖焰
  for (let s = 0; s < 3; s++) {
    const y = (s - 1) * Math.max(1, ry * 0.4);
    const len = Math.max(2, Math.round(rx * (0.18 + 0.1 * hash01(s, seed + 71))));
    p.line(cx - rx * 0.7, cy + y, cx - rx * 0.7 - len, cy + y + (s - 1) * 0.6, C[4], 0.75);
  }
}

// ---- 竖立光刃：竖向新月，锋缘在右，帧间摆动
function drawBlade(p, i, n, box, C, seed) {
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const hw = box.w / 2 - 1, hh = box.h / 2 - 1;
  const lean = (i - (n - 1) / 2) * 0.55;
  for (let y = -Math.floor(hh); y <= Math.floor(hh); y++) {
    const t = (y + hh) / (2 * hh);
    const prof = Math.pow(Math.sin(Math.PI * t), 0.55);
    const xc = lean + (t - 0.5) * 2.2;
    const left = xc - hw * prof * 0.45;
    const right = xc + hw * prof * 0.72;
    for (let x = Math.floor(left); x <= Math.ceil(right); x++) {
      const q = (x - left) / Math.max(0.6, right - left);
      p.dot(cx + x, cy + y, q > 0.82 ? C[7] : q > 0.58 ? C[6] : q > 0.3 ? C[5] : C[3], 1);
    }
    // 锋缘光屑
    if (y % 2 === 0 && hash01(y + i * 13, seed + 9) < 0.55) {
      const len = 1 + Math.floor(hash01(y + i, seed + 11) * 3);
      p.line(cx + right, cy + y, cx + right + len, cy + y + 1, C[6], 0.8);
    }
  }
  // 两端收尖的亮核
  p.line(cx + lean * 0.2, cy - hh * 0.7, cx - lean * 0.2, cy + hh * 0.7, C[6], 0.7);
}

// ---- 光箭：三角箭头 + 亮芯箭杆 + 尾部能量羽
function drawArrow(p, i, n, box, C, seed) {
  const y = box.y + box.h / 2;
  const x0 = box.x, x1 = box.x + box.w - 1;
  const midY = y;
  const headLen = Math.max(6, Math.min(14, Math.round(box.w * 0.26)));
  const shaftH = Math.max(1, Math.round(box.h * 0.2));
  // 箭杆
  for (let x = x0 + 2; x <= x1 - headLen + 2; x++) {
    for (let d = -shaftH; d <= shaftH; d++) {
      p.dot(x, midY + d, Math.abs(d) < shaftH ? C[6] : C[4], Math.abs(d) <= shaftH ? 1 : 0.5);
    }
  }
  // 箭头
  const tip = x1 - 1;
  for (let t = 0; t <= headLen; t++) {
    const x = tip - t;
    const half = Math.max(1, Math.round((t / headLen) * box.h * 0.42));
    for (let d = -half; d <= half; d++) {
      p.dot(x, midY + d, Math.abs(d) < half * 0.45 ? C[7] : Math.abs(d) < half * 0.8 ? C[6] : C[5], 1);
    }
  }
  // 尾羽
  const tail = x0 + 2;
  for (let s = -1; s <= 1; s += 2) {
    p.line(tail, midY, tail + 5, midY + s * Math.max(2, box.h * 0.3), C[5], 0.9);
    p.line(tail + 2, midY, tail + 6, midY + s * Math.max(1, box.h * 0.18), C[4], 0.7);
  }
  // 相位闪烁：箭头与尾羽的颗粒
  for (let k = 0; k < 6; k++) {
    const x = x0 + Math.round(hash01(k + i * 17, seed + 21) * box.w);
    const dy = (hash01(k + 5, seed + 23) - 0.5) * box.h * 0.5;
    p.dot(x, midY + dy, C[4], 0.45);
  }
}

// ---- 拖尾：沿原框方向分层流线（diag 用于斜向刃路）
function drawTrail(p, i, n, box, C, seed, diag) {
  const vertical = box.h > box.w * 1.05;
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const count = vertical ? 5 : 6;
  if (vertical) {
    for (let s = 0; s < count; s++) {
      const x0 = cx + (hash01(s, seed) - 0.5) * box.w * 0.7;
      const len = box.h * (0.45 + 0.45 * hash01(s + 13, seed + 2));
      const y1 = cy + box.h * 0.45;
      const y0 = Math.max(cy - box.h * 0.5 + 1, y1 - len);
      for (let y = y0; y <= y1; y++) {
        const t = (y - y0) / Math.max(1, y1 - y0);
        const wob = Math.sin(t * 6.2 + i * 1.3 + s) * (1 + hash01(s, seed + 6) * 1.4) * (1 - t * 0.4);
        const thick = 1 + Math.round(1.8 * t);
        for (let d = -thick; d <= thick; d++) {
          const lvl = Math.abs(d) === 0 ? 6 : Math.abs(d) <= 1 ? 5 : 4;
          p.dot(x0 + wob + d, y, t > 0.78 ? C[Math.min(7, lvl + 1)] : C[lvl], Math.abs(d) <= 1 ? 1 : 0.65);
        }
      }
      p.circle(x0, y1, 2.2, C[6], 0.9);
      p.circle(x0, y1, 1, C[7], 1);
    }
    return;
  }
  // 横向：亮端在右，向左渐隐；diag≠0 时整束按刃路倾斜
  const x1 = cx + box.w * 0.44;
  for (let s = 0; s < count; s++) {
    const y0 = cy + (hash01(s, seed) - 0.5) * box.h * 0.8;
    const len = box.w * (0.55 + 0.4 * hash01(s + 13, seed + 2));
    const x0 = Math.max(cx - box.w * 0.5 + 1, x1 - len);
    for (let x = x0; x <= x1; x++) {
      const t = (x - x0) / Math.max(1, x1 - x0);
      const wob = Math.sin(t * 6.2 + i * 1.3 + s) * (1 + hash01(s, seed + 6) * 1.4) * (1 - t * 0.4);
      const tilt = diag ? diag * (t - 0.5) * box.h * 0.5 : 0;
      const thick = 1 + Math.round(1.8 * t);
      for (let d = -thick; d <= thick; d++) {
        const lvl = Math.abs(d) === 0 ? 6 : Math.abs(d) <= 1 ? 5 : 4;
        p.dot(x, y0 + wob + tilt + d, t > 0.78 ? C[Math.min(7, lvl + 1)] : C[lvl], Math.abs(d) <= 1 ? 1 : 0.65);
      }
    }
    const headY = y0 + (diag ? diag * box.h * 0.25 : 0);
    p.circle(x1, headY, 2.2, C[6], 0.9);
    p.circle(x1, headY, 1, C[7], 1);
  }
}

// ---- 命中：椭圆星爆 + 冲击环 + 碎屑，一次性播放
function drawHit(p, i, n, box, C, seed) {
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const rx = Math.max(3, box.w / 2 - 1), ry = Math.max(3, box.h / 2 - 1);
  const grow = [0.4, 0.72, 0.94, 1][Math.min(i, 3)];
  const fade = [1, 1, 0.86, 0.6][Math.min(i, 3)];
  const spikes = 10;
  for (let k = 0; k < spikes; k++) {
    const a = k * TAU / spikes + (hash01(k, seed) - 0.5) * 0.3;
    const len = (0.45 + 0.55 * hash01(k + 31, seed + 3)) * (0.55 + 0.5 * grow);
    const wob = 0.12 * Math.sin(i * 1.7 + k);
    const steps = Math.max(4, Math.round(Math.max(rx, ry) * len));
    for (let t = 1; t <= steps; t++) {
      const u = t / steps, aa = a + wob * u;
      const thick = Math.max(0.7, 2.6 * (1 - u) + 0.4);
      p.circle(cx + Math.cos(aa) * rx * len * u, cy + Math.sin(aa) * ry * len * u,
        thick * 0.85, u > 0.82 ? C[4] : u > 0.5 ? C[5] : C[6], (u > 0.88 ? 0.6 : 1) * fade);
      if (u < 0.45) p.dot(cx + Math.cos(aa) * rx * len * u, cy + Math.sin(aa) * ry * len * u, C[7], 0.45 * fade);
    }
  }
  // 爆心实体：不规则椭圆，给冲击一个质量中心（实心，只在边缘抖）
  const brx = rx * (0.16 + 0.24 * grow), bry = ry * (0.2 + 0.28 * grow);
  p.ellipse(cx, cy, brx, bry, (d, ang) => {
    const rag = 0.82 + 0.18 * noise1(ang * 5 + i * 2.3, seed + 41);
    if (d > rag) return 0;
    const q = d / rag;
    return q < 0.2 ? C[6] : q < 0.52 ? C[5] : q < 0.8 ? C[4] : C[3];
  }, 1);
  // 边缘抖动
  for (let k = 0; k < Math.round((brx + bry) * 1.1); k++) {
    const a = hash01(k + i * 11, seed + 51) * TAU;
    p.dot(cx + Math.cos(a) * brx * 1.04, cy + Math.sin(a) * bry * 1.04, C[3], 0.5);
  }
  // 椭圆冲击环：2–3 px 厚的断续带
  const rg = 0.34 + 0.48 * grow;
  for (let a = 0; a < TAU; a += 0.022) {
    if (hash01(Math.floor(a * 400), seed + i * 13) > 0.7) continue;
    for (let w = 0; w < 3; w++) {
      p.dot(cx + Math.cos(a) * rx * (rg - w * 0.035), cy + Math.sin(a) * ry * (rg - w * 0.035),
        w === 0 ? C[5] : w === 1 ? C[4] : C[3], (w === 0 ? 0.95 : 0.6) * fade);
    }
  }
  const rc = Math.max(2, Math.min(rx, ry) * (0.3 - i * 0.04));
  p.circle(cx, cy, rc * 1.5, C[4], 0.9 * fade);
  p.circle(cx, cy, rc * 0.85, C[6], fade);
  p.circle(cx, cy, Math.max(1, rc * 0.4), C[7], fade);
  const cnt = Math.min(64, Math.round((rx + ry) * 0.5));
  for (let k = 0; k < cnt; k++) {
    const a = hash01(k * 3, seed + 7) * TAU;
    const rad = 0.28 + 0.85 * hash01(k * 5, seed + 9);
    const px = cx + Math.cos(a) * rx * rad * grow, py = cy + Math.sin(a) * ry * rad * grow;
    p.circle(px, py, hash01(k + 11, seed + 19) > 0.6 ? 1.3 : 0.8,
      C[3 + (k % 2)], (0.45 + 0.4 * hash01(k + 3, seed + 17)) * fade);
  }
}

const DRAWERS = {
  charge: (p, f, i, n, C, seed) => drawCharge(p, i, n, f.R, C, seed, f.oneshot),
  beam: (p, f, i, n, C, seed) => drawBeam(p, i, n, f.boxes[i], C, seed, f.fan),
  orb: (p, f, i, n, C, seed) => drawOrb(p, i, n, f.boxes[i], C, seed),
  bolt: (p, f, i, n, C, seed) => drawBolt(p, i, n, f.boxes[i], C, seed),
  blade: (p, f, i, n, C, seed) => drawBlade(p, i, n, f.boxes[i], C, seed),
  arrow: (p, f, i, n, C, seed) => drawArrow(p, i, n, f.boxes[i], C, seed),
  trail: (p, f, i, n, C, seed) => drawTrail(p, i, n, f.boxes[i], C, seed, 0),
  trail_diag: (p, f, i, n, C, seed) => drawTrail(p, i, n, f.boxes[i], C, seed, 1),
  hit: (p, f, i, n, C, seed) => drawHit(p, i, n, f.boxes[i], C, seed),
};

// ---- 烘焙
const spec = JSON.parse(readFileSync(0, 'utf8'));
const report = { character: spec.character, families: [] };
for (const fam of spec.families) {
  const draw = DRAWERS[fam.kind];
  if (!draw) throw Error(`未知形状 ${fam.kind}（${fam.name}）`);
  const C = fit(fam.palette, 8);
  const n = fam.frames.length;
  const W = fam.width, H = fam.height;
  const boxes = fam.frames.map((f) => ({ x: f.art[0], y: f.art[1], w: f.art[2], h: f.art[3] }));
  const maxR = Math.max(...boxes.map((b) => Math.max(b.w, b.h) / 2));
  const R = Math.max(6, Math.min(maxR, Math.min(W, H) / 2 - 2));
  const ctx = { boxes, R, oneshot: !!fam.oneshot, fan: !!fam.fan };
  const dir = join(OUT, fam.out);
  mkdirSync(dir, { recursive: true });
  // 画布尺寸取 rects 的外接范围，帧按原始 rect 坐标贴回。
  let cw = 0, ch = 0;
  for (const r of fam.rects) { cw = Math.max(cw, r[0] + r[2]); ch = Math.max(ch, r[1] + r[3]); }
  const atlas = new Uint8ClampedArray(cw * ch * 4);
  const frameHashes = [];
  for (let i = 0; i < n; i++) {
    const frame = createFrame(W, H);
    const p = painterFor(frame).place(fam.anchor[0], fam.anchor[1]);
    draw(p, ctx, i, n, C, fam.seed);
    const rgba = composite(frame, new Uint8ClampedArray(W * H * 4), null);
    let visible = 0;
    for (let j = 0; j < rgba.length; j += 4) {
      if (rgba[j + 3] !== 0) { rgba[j + 3] = 255; visible++; }
      else { rgba[j] = rgba[j + 1] = rgba[j + 2] = 0; }
    }
    if (!visible) throw Error(`${fam.name} 第 ${i} 帧为空`);
    const png = encodePNG(W, H, rgba);
    writeFileSync(join(dir, 'frame-' + i + '.png'), png);
    frameHashes.push(SHA(png));
    const [rx, ry] = fam.rects[i];
    for (let row = 0; row < H; row++) {
      atlas.set(rgba.subarray(row * W * 4, (row + 1) * W * 4), ((ry + row) * cw + rx) * 4);
    }
  }
  const atlasPng = encodePNG(cw, ch, atlas);
  writeFileSync(join(dir, 'atlas.png'), atlasPng);
  report.families.push({
    name: fam.name, out: fam.out, kind: fam.kind, seed: fam.seed,
    canvas: [cw, ch], frame_size: [W, H], anchor: fam.anchor, rects: fam.rects,
    palette: fam.palette, frame_sha256: frameHashes, atlas_sha256: SHA(atlasPng),
  });
  console.log(`  ${fam.name}: ${fam.kind} ${W}x${H} ×${n}`);
}
writeFileSync(join(OUT, 'bake.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ out: OUT, families: report.families.length }));
