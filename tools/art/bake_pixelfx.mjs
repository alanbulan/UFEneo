#!/usr/bin/env node
/**
 * Deterministic offline composition of the vendored PixelFX modules.
 *
 * node tools/art/bake_pixelfx.mjs --all --write
 * node tools/art/bake_pixelfx.mjs --all --check
 * node tools/art/bake_pixelfx.mjs --recipe zoffy_fx_frost_cone --write
 *
 * No Godot, actors, generated character art, runtime scaling, or credentials.
 * Recipes and source hashes live with each registry entry; PNGs stay local.
 * All visible shapes originate in the existing PixelFX modules. Composition
 * only selects their particle layers, places/crops them, and quantizes alpha.
 */
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateSync } from 'node:zlib';
import { loadEffect, renderFrames } from '../../third_party/pixelfx/tools/lib/fxlib.mjs';
import { encodePNG } from '../../third_party/pixelfx/tools/lib/png.mjs';

const TOOL = fileURLToPath(import.meta.url);
const ROOT = realpathSync(resolve(dirname(TOOL), '../..'));
const REGISTRY = join(ROOT, 'content/presentation/phase3_projectiles.json');
const OUTPUT = join(ROOT, 'assets/fx/phase3');
const ICE = ['#102e47', '#225574', '#397d9b', '#62adc6', '#a1dce6', '#d9f5f3', '#ffffff'];
const ZAP = ['#09294b', '#145585', '#237faa', '#50bdd6', '#9beaf2', '#dbfbfa', '#ffffff'];
const RECIPES = {
  zoffy_fx_frost_flight: {
    kind: 'mist_projectile', seed: 605152, cell: [88, 64], anchor: [44, 32],
    frames: 8, ticks: 3, loop: true, palette: ICE,
    description: 'Compact cold mist and suspended crystal chips; no laser core or three parallel rays.',
  },
  zoffy_fx_frost_cone: {
    kind: 'mist_cone', seed: 605153, cell: [64, 56], anchor: [6, 28],
    frames: 12, ticks: 2, loop: true, palette: ICE, max_reach: 44,
    description: 'Near-hand cold mist only (at most 44 native pixels); the separate travelling cloud carries damage.',
  },
  zoffy_fx_air_zap_beam: {
    kind: 'diagonal_beam', seed: 605154, cell: [272, 168], anchor: [16, 24],
    frames: 8, ticks: 1, loop: false, palette: ZAP,
    length: 260, direction: [2, 1], half_width: 11,
    description: 'Airborne Z electric beam, authored diagonally down-right; 260 native pixels along its axis.',
  },
  zoffy_fx_m87_beam: {
    kind: 'native_reach', seed: null, cell: [592, 120], anchor: [18, 60],
    frames: 36, ticks: 1, loop: false,
    source_atlas: 'art/fighters/zoffy/fx/m87_beam-source.png',
    source_sha256: 'bf204cbc1268cfd494fc097d72662d9c4ef9f182a77d89e770d133c53d95cf74',
    source_cell: [640, 120], source_columns: 4, cut_columns: [160, 48], max_reach: 560,
    description: 'Preserve every original PixelFX material pixel except 48 columns of common straight shaft; never resize, repaint, or change timing.',
  },
  zoffy_fx_barrier: {
    kind: 'barrier', seed: 605155, cell: [90, 128], anchor: [8, 64],
    frames: 8, ticks: 2, loop: true, palette: ZAP,
    visible_bounds: [0, -56, 74, 112],
    description: 'Six existing PixelFX electric-beam strips form a forward hexagonal wall, matching the existing interception box; no Q aura.',
  },
};
const cache = new Map();
const hash = data => createHash('sha256').update(data).digest('hex');
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const BAYER = [0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
  12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
  3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
  15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21];

function insideRoot(path) {
  const rel = relative(ROOT, resolve(path));
  if (rel === '..' || rel.startsWith(`..${sep}`) || rel.startsWith(sep)) {
    throw new Error(`Output is outside repository: ${path}`);
  }
  let parent = existsSync(path) ? path : dirname(path);
  while (!existsSync(parent)) parent = dirname(parent);
  const real = relative(ROOT, realpathSync(parent));
  if (real === '..' || real.startsWith(`..${sep}`) || real.startsWith(sep)) {
    throw new Error(`Output parent resolves outside repository: ${path}`);
  }
  return path;
}

function hexColor(text) {
  return [1, 3, 5].map(offset => Number.parseInt(text.slice(offset, offset + 2), 16));
}

function blank(width, height) {
  return { width, height, data: new Uint8ClampedArray(width * height * 4) };
}

function over(target, x, y, color, opacity = 1) {
  x = Math.round(x); y = Math.round(y);
  if (x < 0 || y < 0 || x >= target.width || y >= target.height) return;
  const a = clamp(color[3] / 255 * opacity, 0, 1);
  if (a <= 0) return;
  const i = (y * target.width + x) * 4, old = target.data[i + 3] / 255;
  const next = a + old * (1 - a);
  for (let channel = 0; channel < 3; channel++) {
    target.data[i + channel] = (color[channel] * a + target.data[i + channel] * old * (1 - a)) / next;
  }
  target.data[i + 3] = 255 * next;
}

async function source(id, seed, palette, softOnly = false) {
  const key = JSON.stringify([id, seed, palette, softOnly]);
  if (cache.has(key)) return cache.get(key);
  const fx = await loadEffect(id);
  let mod = fx.mod;
  if (softOnly) {
    if (id !== 'impacts/bullet-impact') throw new Error('Only the impact module exports soft particle layers.');
    const original = fx.mod;
    mod = {
      meta: original.meta,
      create(options) {
        const live = original.create(options);
        return { update: dt => live.update(dt), draw: painter => live.drawBack(painter) };
      },
    };
  }
  const rendered = renderFrames({ ...fx, mod }, {
    fps: 60, seed, actor: false, bg: 'none',
    options: { palette, stone: '#89b9cc', height: 24, seed },
  });
  cache.set(key, rendered);
  return rendered;
}

function frameAt(rendered, seconds) {
  return rendered.frames[clamp(Math.round(seconds * rendered.fps), 0, rendered.n - 1)].clear;
}

/** Mirror only PixelFX's emitted particles; exclude its wall scar and impact star. */
function placeMist(target, rendered, seconds, at, scale, opacity, mask) {
  const pixels = frameAt(rendered, seconds);
  const x0 = 116, y0 = 60;
  const left = Math.max(0, Math.floor(at[0]));
  const right = Math.min(target.width - 1, Math.ceil(at[0] + 72 * scale[0]));
  const top = Math.max(0, Math.floor(at[1] - 38 * scale[1]));
  const bottom = Math.min(target.height - 1, Math.ceil(at[1] + 30 * scale[1]));
  for (let y = top; y <= bottom; y++) {
    for (let x = left; x <= right; x++) {
      const sx = Math.round(x0 - (x - at[0]) / scale[0]);
      const sy = Math.round(y0 + (y - at[1]) / scale[1]);
      if (sx < 36 || sx > 113 || sy < 20 || sy > 88) continue;
      const i = (sy * rendered.w + sx) * 4;
      if (!pixels[i + 3]) continue;
      const weight = mask ? mask(x, y) : 1;
      if (weight > 0) over(target, x, y, pixels.subarray(i, i + 4), opacity * weight);
    }
  }
}

async function mistFrame(recipe, index) {
  const target = blank(...recipe.cell), [ax, ay] = recipe.anchor;
  const phase = index / recipe.frames;
  if (recipe.kind === 'mist_projectile') {
    // Several distinct seeded puffs form one compact, irregular cloud.
    const layers = [
      [-29, -5, 1.15, 1.2], [-24, 3, 1.1, 1.3], [-16, -1, 0.95, 1.1],
      [-9, 2, 0.9, 0.95], [-20, -6, 1.0, 1.15],
    ];
    for (let i = 0; i < layers.length; i++) {
      const [x, y, sx, sy] = layers[i];
      const cloud = await source('impacts/bullet-impact', recipe.seed + i, recipe.palette, true);
      const age = 0.14 + ((phase + i * 0.173) % 1) * 0.27;
      placeMist(target, cloud, age, [ax + x, ay + y], [sx, sy], 1.9,
        (px, py) => clamp((1 - Math.max(0, Math.abs(px - ax) - 18) / 16) * (1 - Math.max(0, Math.abs(py - ay) - 14) / 12), 0, 1));
    }
    const chips = await source('impacts/bullet-impact', recipe.seed + 29, recipe.palette);
    placeMist(target, chips, 0.17 + phase * 0.10, [ax - 17, ay + 1], [0.63, 0.64], 0.75,
      (x, y) => Math.abs(x - ax) <= 25 && Math.abs(y - ay) <= 21 ? 1 : 0);
  } else {
    // Expanding layers of the module's dust/smoke, not copies of a beam body.
    const mask = (x, y) => {
      const dx = x - ax, dy = Math.abs(y - ay);
      if (dx < 0 || dx > recipe.max_reach || dy > 3 + dx * 0.29) return 0;
      return clamp((1 - Math.max(0, dx - 35) / 10) * (1 - Math.max(0, dy - (1 + dx * 0.23)) / 5), 0, 1);
    };
    for (let band = 0; band < 5; band++) {
      for (let lane = -1; lane <= 1; lane++) {
        const i = band * 3 + lane + 1;
        const cloud = await source('impacts/bullet-impact', recipe.seed + i, recipe.palette, true);
        const age = 0.14 + ((phase + i * 0.137) % 1) * 0.26;
        const x = ax + band * 7 - 4 + phase * 2;
        const y = ay + lane * (1 + band * 2);
        placeMist(target, cloud, age, [x, y], [0.75, 0.75 + band * 0.06], 1.65, mask);
      }
    }
    for (let i = 0; i < 3; i++) {
      const chips = await source('impacts/bullet-impact', recipe.seed + 37 + i, recipe.palette);
      placeMist(target, chips, 0.16 + ((phase + i * 0.31) % 1) * 0.15,
        [ax + 4 + i * 11, ay + (i - 1) * 3], [0.35, 0.4], 0.7, mask);
    }
  }
  return target;
}

async function beamFrame(recipe, index) {
  const target = blank(...recipe.cell);
  const beam = await source('arcane/arcane-beam', recipe.seed, recipe.palette);
  const pixels = frameAt(beam, index / recipe.frames * 1.2);
  const norm = Math.hypot(...recipe.direction), cos = recipe.direction[0] / norm, sin = recipe.direction[1] / norm;
  const envelope = [0.45, 0.75, 1, 1, 1, 0.85, 0.6, 0.35][index];
  for (let y = 0; y < target.height; y++) {
    for (let x = 0; x < target.width; x++) {
      const dx = x - recipe.anchor[0], dy = y - recipe.anchor[1];
      const along = dx * cos + dy * sin, across = -dx * sin + dy * cos;
      if (along < -8 || along > recipe.length || Math.abs(across) > recipe.half_width * envelope + 3) continue;
      // Native body tiles are composed offline; neither Godot nor the clip scales.
      let u;
      if (along < 12) u = along;
      else if (along > recipe.length - 12) u = 168 - (recipe.length - along);
      else u = 12 + ((Math.floor(along) - 12) % 144);
      const sx = clamp(Math.round(41 + u), 0, beam.w - 1);
      const sy = clamp(Math.round(60 + across / (1.1 * envelope)), 0, beam.h - 1);
      const i = (sy * beam.w + sx) * 4;
      const end = clamp((recipe.length - along + 1) / 5, 0, 1);
      over(target, x, y, pixels.subarray(i, i + 4), end);
    }
  }
  return target;
}

async function barrierFrame(recipe, index) {
  const target = blank(...recipe.cell);
  const beam = await source('arcane/arcane-beam', recipe.seed, recipe.palette);
  const pixels = frameAt(beam, index / recipe.frames * 1.2);
  // Placement of module strips, not newly drawn polygon pixels. The outer
  // bounds deliberately coincide with the unchanged simulation rectangle.
  const vertices = [[37, -56], [73, -32], [73, 31], [37, 55], [0, 31], [0, -32]];
  for (let y = 0; y < target.height; y++) {
    for (let x = 0; x < target.width; x++) {
      const px = x - recipe.anchor[0], py = y - recipe.anchor[1];
      const [bx, by, bw, bh] = recipe.visible_bounds;
      if (px < bx || px >= bx + bw || py < by || py >= by + bh) continue;
      for (let edge = 0; edge < vertices.length; edge++) {
        const a = vertices[edge], b = vertices[(edge + 1) % vertices.length];
        const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy);
        const along = ((px - a[0]) * dx + (py - a[1]) * dy) / length;
        const across = (-(px - a[0]) * dy + (py - a[1]) * dx) / length;
        if (along < -1 || along > length + 1 || Math.abs(across) > 2.6) continue;
        const sx = 41 + 12 + ((Math.round(along) + edge * 19 + 144) % 144);
        const sy = clamp(Math.round(60 + across / 0.35), 0, beam.h - 1);
        const i = (sy * beam.w + sx) * 4;
        over(target, x, y, pixels.subarray(i, i + 4));
      }
    }
  }
  return target;
}

/** Read a SHA-pinned RGBA PNG without dependencies or a second script. */
function readNativeAtlas(recipe) {
  const key = `native:${recipe.source_atlas}`;
  if (cache.has(key)) return cache.get(key);
  const file = insideRoot(join(ROOT, recipe.source_atlas));
  const bytes = readFileSync(file);
  if (hash(bytes) !== recipe.source_sha256) throw new Error('Frozen native source SHA does not match the recipe.');
  if (bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error('Invalid PNG signature.');
  let width = 0, height = 0;
  const chunks = [];
  for (let offset = 8; offset < bytes.length;) {
    const length = bytes.readUInt32BE(offset), type = bytes.subarray(offset + 4, offset + 8).toString('ascii');
    const payload = bytes.subarray(offset + 8, offset + 8 + length);
    if (offset + length + 12 > bytes.length) throw new Error('Truncated source PNG.');
    if (type === 'IHDR') {
      width = payload.readUInt32BE(0); height = payload.readUInt32BE(4);
      if (payload[8] !== 8 || payload[9] !== 6 || payload[10] || payload[11] || payload[12]) {
        throw new Error('Native material must be a noninterlaced 8-bit RGBA PNG.');
      }
    } else if (type === 'IDAT') chunks.push(payload);
    offset += length + 12;
  }
  if (!width || !height || !chunks.length) throw new Error('Incomplete source PNG.');
  const raw = inflateSync(Buffer.concat(chunks)), stride = width * 4;
  if (raw.length !== (stride + 1) * height) throw new Error('Unexpected source PNG scanline length.');
  const result = blank(width, height);
  const paeth = (a, b, c) => {
    const p = a + b - c, aa = Math.abs(p - a), bb = Math.abs(p - b), cc = Math.abs(p - c);
    return aa <= bb && aa <= cc ? a : bb <= cc ? b : c;
  };
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    if (filter > 4) throw new Error('Unknown PNG row filter.');
    for (let x = 0; x < stride; x++) {
      const at = y * stride + x;
      const a = x >= 4 ? result.data[at - 4] : 0;
      const b = y ? result.data[at - stride] : 0;
      const c = x >= 4 && y ? result.data[at - stride - 4] : 0;
      const predictor = [0, a, b, Math.floor((a + b) / 2), paeth(a, b, c)][filter];
      result.data[at] = (raw[y * (stride + 1) + 1 + x] + predictor) & 255;
      if (x % 4 === 3 && result.data[at] !== 0 && result.data[at] !== 255) {
        throw new Error('Frozen material has nonbinary alpha.');
      }
    }
  }
  cache.set(key, result);
  return result;
}

function nativeFrame(recipe, index) {
  const source = readNativeAtlas(recipe), target = blank(...recipe.cell);
  const [sw, sh] = recipe.source_cell, [cut, removed] = recipe.cut_columns;
  if (sw - removed !== target.width || sh !== target.height || source.width !== sw * recipe.source_columns) {
    throw new Error('Native reach recipe dimensions do not match the frozen source.');
  }
  const ox = (index % recipe.source_columns) * sw, oy = Math.floor(index / recipe.source_columns) * sh;
  if (oy + sh > source.height || cut < 0 || cut + removed >= sw) throw new Error('Native source rectangle is out of range.');
  for (let y = 0; y < sh; y++) {
    const row = ((oy + y) * source.width + ox) * 4;
    target.data.set(source.data.subarray(row, row + cut * 4), y * target.width * 4);
    target.data.set(source.data.subarray(row + (cut + removed) * 4, row + sw * 4), (y * target.width + cut) * 4);
  }
  return target;
}

function quantize(frame, palette) {
  const colors = palette.map(hexColor);
  for (let y = 0; y < frame.height; y++) {
    for (let x = 0; x < frame.width; x++) {
      const i = (y * frame.width + x) * 4;
      const threshold = (BAYER[(y % 8) * 8 + (x % 8)] + 0.5) * 255 / 64;
      if (frame.data[i + 3] < 24 || frame.data[i + 3] < threshold) {
        frame.data.fill(0, i, i + 4);
        continue;
      }
      let chosen = colors[0], distance = Infinity;
      for (const color of colors) {
        const delta = (color[0] - frame.data[i]) ** 2 + (color[1] - frame.data[i + 1]) ** 2 + (color[2] - frame.data[i + 2]) ** 2;
        if (delta < distance) { distance = delta; chosen = color; }
      }
      frame.data.set([...chosen, 255], i);
    }
  }
  return frame;
}

function bounds(frame, anchor, preserveLeftEdge = false) {
  let x0 = frame.width, y0 = frame.height, x1 = -1, y1 = -1, count = 0;
  for (let y = 0; y < frame.height; y++) {
    for (let x = 0; x < frame.width; x++) {
      if (!frame.data[(y * frame.width + x) * 4 + 3]) continue;
      x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); count++;
    }
  }
  if (!count) throw new Error('PixelFX composition produced an empty frame.');
  if ((!preserveLeftEdge && x0 === 0) || y0 === 0 || x1 === frame.width - 1 || y1 === frame.height - 1) {
    throw new Error('PixelFX composition touches the cell edge; enlarge the recipe cell.');
  }
  return { box: [x0 - anchor[0], y0 - anchor[1], x1 - x0 + 1, y1 - y0 + 1], count };
}

function atlasFor(frames) {
  const columns = Math.min(4, frames.length), rows = Math.ceil(frames.length / columns);
  const [width, height] = [frames[0].width, frames[0].height];
  const atlas = blank(columns * width, rows * height), rects = [];
  for (let index = 0; index < frames.length; index++) {
    const x = (index % columns) * width, y = Math.floor(index / columns) * height;
    rects.push([x, y, width, height]);
    for (let row = 0; row < height; row++) {
      const start = row * width * 4;
      atlas.data.set(frames[index].data.subarray(start, start + width * 4), ((y + row) * atlas.width + x) * 4);
    }
  }
  return { atlas, rects };
}

function sourcesFor(recipe) {
  if (recipe.kind === 'native_reach') {
    return [{ path: recipe.source_atlas, sha256: recipe.source_sha256, operation: 'Lossless reflow of existing offline-baked PixelFX material; no palette remap.' }];
  }
  const ids = ['diagonal_beam', 'barrier'].includes(recipe.kind) ? ['arcane/arcane-beam'] : ['impacts/bullet-impact'];
  return ids.map(id => ({
    id,
    path: `res://third_party/pixelfx/src/fx/${id}.js`,
    sha256: hash(readFileSync(join(ROOT, 'third_party/pixelfx/src/fx', `${id}.js`))),
  }));
}

async function bake(id) {
  const recipe = RECIPES[id];
  const frames = [];
  for (let index = 0; index < recipe.frames; index++) {
    if (recipe.kind === 'native_reach') frames.push(nativeFrame(recipe, index));
    else {
      const frame = await (recipe.kind === 'diagonal_beam' ? beamFrame(recipe, index)
        : recipe.kind === 'barrier' ? barrierFrame(recipe, index) : mistFrame(recipe, index));
      frames.push(quantize(frame, recipe.palette));
    }
  }
  const boxes = frames.map(frame => bounds(frame, recipe.anchor, recipe.kind === 'native_reach'));
  if (recipe.max_reach && boxes.some(value => value.box[0] + value.box[2] - 1 > recipe.max_reach)) {
    throw new Error(`${id}: visible material exceeds its native reach limit.`);
  }
  if (recipe.kind === 'barrier' && boxes.some(value => JSON.stringify(value.box) !== JSON.stringify(recipe.visible_bounds))) {
    throw new Error(`${id}: visible barrier does not match its unchanged interception bounds.`);
  }
  const { atlas, rects } = atlasFor(frames);
  const png = encodePNG(atlas.width, atlas.height, atlas.data);
  const path = insideRoot(join(OUTPUT, 'zoffy', `${id.replace(/^zoffy_fx_/, '')}.png`));
  return {
    path, png,
    entry: {
      id, texture: `res://${relative(ROOT, path).split(sep).join('/')}`, rects,
      anchor: recipe.anchor, ticks: recipe.ticks, loop: recipe.loop,
      visual_scale: 1, display_scale: [1, 1], alpha_binary: true,
      color_parameter: true, source_kind: 'pixelfx_code_baked', license: 'MIT',
      dedicated_to: 'zoffy', orientation: 'authored',
      ...(['diagonal_beam', 'native_reach'].includes(recipe.kind) ? { full_frame: true, emission_anchor: true } : {}),
      atlas_sha256: hash(png), frame_boxes: boxes.map(value => value.box),
      bake: {
        tool: 'res://tools/art/bake_pixelfx.mjs', tool_sha256: hash(readFileSync(TOOL)),
        recipe: JSON.parse(JSON.stringify(recipe)), sources: sourcesFor(recipe),
        pixel_operation: recipe.kind === 'native_reach'
          ? 'Lossless removal of the stated shaft columns from frozen PixelFX material; both ends, original palette, binary alpha, and per-phase timing remain unchanged.'
          : 'Existing PixelFX particle-layer / beam-frame composition, nearest-neighbour native raster, fixed Bayer alpha and shared seven-color quantization.',
        alpha_values: [0, 255], frame_rgba_sha256: frames.map(frame => hash(frame.data)),
        visible_pixels: boxes.map(value => value.count),
        ...(recipe.kind === 'diagonal_beam' ? { endpoint_from_emission: [232, 116], coordinate_system: 'Image: +x right, +y down. Simulation endpoint: [232,-116].' } : {}),
        review_status: 'pending_root_runtime_review',
      },
    },
  };
}

function replaceEntry(text, id, entry) {
  const key = `  ${JSON.stringify(id)}: `;
  const start = text.indexOf(key);
  const formatted = JSON.stringify(entry, null, 2).split('\n').map((line, index) => index ? `  ${line}` : line).join('\n');
  if (start < 0) {
    const closing = text.lastIndexOf('\n}');
    if (closing < 0) throw new Error('Registry must be a formatted JSON object.');
    return `${text.slice(0, closing)},\n${key}${formatted}${text.slice(closing)}`;
  }
  let at = start + key.length, depth = 0, quoted = false, escaped = false;
  for (; at < text.length; at++) {
    const char = text[at];
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') quoted = false;
    } else if (char === '"') quoted = true;
    else if (char === '{' || char === '[') depth++;
    else if (char === '}' || char === ']') {
      depth--;
      if (depth === 0) return text.slice(0, start + key.length) + formatted + text.slice(at + 1);
    }
  }
  throw new Error(`Unterminated registry entry: ${id}`);
}

async function main() {
  const args = process.argv.slice(2), ids = [];
  let write = false, check = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--all') ids.push(...Object.keys(RECIPES));
    else if (args[i] === '--recipe') ids.push(args[++i]);
    else if (args[i] === '--write') write = true;
    else if (args[i] === '--check') check = true;
    else throw new Error(`Unknown argument: ${args[i]}`);
  }
  if (!ids.length || write === check) throw new Error('Choose --all or --recipe <id> and exactly one of --write / --check.');
  insideRoot(REGISTRY);
  if (!existsSync(join(ROOT, 'AGENTS.md')) || !existsSync(join(ROOT, 'third_party/pixelfx'))) {
    throw new Error('Tool is not inside the expected project root.');
  }
  let text = readFileSync(REGISTRY, 'utf8');
  const registry = JSON.parse(text);
  for (const id of [...new Set(ids)]) {
    if (!RECIPES[id]) throw new Error(`Unknown recipe: ${id}`);
    const result = await bake(id);
    if (check) {
      if (!existsSync(result.path) || hash(readFileSync(result.path)) !== result.entry.atlas_sha256) {
        throw new Error(`${id}: installed PNG is not reproducible from this recipe.`);
      }
      if (JSON.stringify(registry[id]) !== JSON.stringify(result.entry)) throw new Error(`${id}: registry does not match baked data.`);
    } else {
      insideRoot(result.path);
      mkdirSync(dirname(result.path), { recursive: true });
      writeFileSync(result.path, result.png);
      text = replaceEntry(text, id, result.entry);
    }
    console.log(JSON.stringify({ id, mode: check ? 'check' : 'write', texture: result.entry.texture, frames: result.entry.rects.length, sha256: result.entry.atlas_sha256, frame_boxes: result.entry.frame_boxes }));
  }
  if (write) {
    JSON.parse(text);
    writeFileSync(REGISTRY, text);
  }
}

main().catch(error => { console.error(error.stack ?? error); process.exitCode = 1; });
