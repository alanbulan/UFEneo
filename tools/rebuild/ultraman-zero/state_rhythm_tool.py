#!/usr/bin/env python3
"""赛罗状态帧节奏批：把 1024x1536 像素源落到 256 格并登记。

沿用 README 既有管线：固定比例 0.171689497717（188/1095）、
forge_backend._kcentroid_downscale(detail_bias=False)、Alpha128 硬化、
整图 RGB 最近色映射到冻结 32 色板、root [128,248]、接地脚底 247。

子命令：
  land --manifest 清单.json   落格 + cells.json state_frames_2026_11_10 增帧
  sheet --names ... --out 输出.png   2x 联系表
清单条目：
  {"clip":"idle","index":1,"name":"idle-01","source":"art/.../idle-01-raw.png",
   "generation_id":"image-...","prompt":"...","foot_row":247}
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path.insert(0, str(ROOT / "tools/rebuild/shared"))
import forge_backend  # noqa: E402

CELL = 256
ROOT_PT = (128, 248)
GROUND_FOOT_ROW = 247
SCALE = 0.171689497717
TARGET_STANDING = 188
CELLS_JSON = ROOT / "art/fighters/ultraman-zero/stage1/cells/cells.json"
BLOCK = "state_frames_2026_11_10"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()

def load_palette() -> list:
    d = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    return [tuple(int(v) for v in c) for c in d["palette"]]

def largest_component(mask: np.ndarray) -> np.ndarray:
    from collections import deque
    seen = np.zeros_like(mask, bool); best: list = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)]); seen[y, x] = True; comp = []
            while q:
                cy, cx = q.popleft(); comp.append((cy, cx))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            if len(comp) > len(best):
                best = comp
    out = np.zeros_like(mask, bool)
    for y, x in best:
        out[y, x] = True
    return out

def land_one(entry: dict, palette: list, out_dir: Path) -> dict:
    src = ROOT / entry["source"]
    im = Image.open(src).convert("RGBA")
    # 比例缩放（先裁到内容 bbox，保持与身份锚同口径：锚 trimmed 1095 → 188）
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a >= 128)
    crop = im.crop((int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1))
    tw = max(1, round(crop.width * SCALE))
    th = max(1, round(crop.height * SCALE))
    scaled = forge_backend._kcentroid_downscale(crop, tw, th, detail_bias=False)
    arr = np.array(scaled).copy()
    arr[:, :, 3] = np.where(arr[:, :, 3] >= 128, 255, 0)  # Alpha128 硬化
    scaled = Image.fromarray(arr, "RGBA")
    # 整图最近色映射（palette_mode('rgb') 口径：RGB 欧氏最近，Alpha 独立保存）
    pixels = np.array(scaled)
    visible = pixels[:, :, 3] >= 128
    colors = np.asarray([(int(c[0]), int(c[1]), int(c[2])) for c in palette], dtype=np.int32)
    unique, inverse = np.unique(pixels[..., :3].reshape(-1, 3), axis=0, return_inverse=True)
    nearest = np.empty(len(unique), dtype=np.intp)
    for start in range(0, len(unique), 8192):
        delta = unique[start:start+8192, None].astype(np.int32)-colors
        nearest[start:start+8192] = np.einsum('nki,nki->nk', delta, delta).argmin(axis=1)
    result = pixels.copy()
    result[..., :3] = colors[nearest[inverse]].reshape(pixels.shape[:2]+(3,))
    result[..., 3] = 255
    result[~visible] = 0
    scaled = Image.fromarray(result, "RGBA")
    # 主体最大连通块（非技能帧整帧单连通）
    m = arr[:, :, 3] > 0
    keep = largest_component(m)
    removed = int((m & ~keep).sum())
    if removed:
        arr2 = np.array(scaled).copy()
        arr2[:, :, 3] = np.where(keep, arr2[:, :, 3], 0)
        scaled = Image.fromarray(arr2, "RGBA")
    fa = np.array(scaled)[:, :, 3]
    ys, xs = np.where(fa > 0)
    height = int(ys.max()-ys.min()+1); width = int(xs.max()-xs.min()+1)
    foot_row = int(entry.get("foot_row", GROUND_FOOT_ROW))
    # 脚行（底部 8% 带）中心对 root x
    band_top = int(ys.max() - max(2, round(height*0.08)))
    band = fa[band_top:ys.max()+1]
    bys, bxs = np.where(band > 0)
    center = float(bxs.mean()) if len(bxs) else float((xs.min()+xs.max())/2)
    left = int(round(ROOT_PT[0] - center))
    # 4px 边距水平限位
    if left < 4: left = 4
    if left + width - 1 > CELL-5: left = CELL-5-width
    canvas = Image.new("RGBA", (CELL, CELL), (0,0,0,0))
    canvas.alpha_composite(scaled, (left, foot_row - (int(ys.max()) - int(ys.min()))))
    out = out_dir / f"{entry['name']}-cell.png"
    canvas.save(out)
    # x4 预览
    prev = canvas.resize((CELL*4, CELL*4), Image.NEAREST)
    prev_path = out_dir / f"{entry['name']}-x4.png"
    prev.save(prev_path)
    ca = np.array(canvas)[:, :, 3]
    vys, vxs = np.where(ca > 0)
    colors = int(len(np.unique(np.array(canvas)[:, :, :3][ca > 0], axis=0)))
    comps_mask = ca > 0
    from collections import deque
    seen = np.zeros_like(comps_mask, bool); comps = 0
    h, w = comps_mask.shape
    for y in range(h):
        for x in range(w):
            if comps_mask[y, x] and not seen[y, x]:
                comps += 1
                q = deque([(y, x)]); seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < h and 0 <= nx < w and comps_mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
    rec = {
        "clip": entry["clip"], "frame": int(entry["index"]), "name": entry["name"],
        "role": entry.get("role", ""), "source": entry["source"],
        "source_sha256": sha256(src), "generation_id": entry.get("generation_id"),
        "prompt": entry.get("prompt"), "scale": SCALE,
        "scale_source": "fixed_188_over_anchor_trimmed_1095",
        "output": rel(out), "output_sha256": sha256(out),
        "preview": rel(prev_path), "preview_sha256": sha256(prev_path),
        "height": int(vys.max()-vys.min()+1), "width": int(vxs.max()-vxs.min()+1),
        "bbox_inclusive": [int(vxs.min()), int(vys.min()), int(vxs.max()), int(vys.max())],
        "foot_row": foot_row, "grounded": foot_row == GROUND_FOOT_ROW,
        "colors": colors, "components": comps,
        "alpha": [int(ca.min()), int(ca.max())],
        "cropped_pixels": 0 if (left >= 0 and left+width <= CELL and foot_row-(int(vys.max())-int(vys.min())) >= 0) else -1,
        "removed_nonmax_pixels": removed,
    }
    # 硬门
    rec["hard_gates"] = {
        "components_1": comps == 1,
        "alpha_binary": [int(ca.min()), int(ca.max())] == [0, 255],
        "colors_le_32": colors <= 32,
        "standing_gate": bool(entry.get("standing", True)) and abs(rec["height"]-TARGET_STANDING) <= TARGET_STANDING*0.08 if entry.get("standing", True) else None,
        "fits_cell": rec["bbox_inclusive"][0] >= 0 and rec["bbox_inclusive"][2] < CELL and rec["bbox_inclusive"][3] <= GROUND_FOOT_ROW and rec["bbox_inclusive"][1] >= 0,
    }
    rec["rejects"] = [k for k, v in rec["hard_gates"].items() if v is False]
    rec["status"] = "accepted" if not rec["rejects"] else "rejected"
    if rec["status"] == "rejected":
        out.unlink(missing_ok=True)
        prev_path.unlink(missing_ok=True)
    return rec

def merge_cells(records: list) -> None:
    data = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    block = data.setdefault(BLOCK, {})
    frames = {f["name"]: f for f in block.get("frames", [])}
    for r in records:
        frames[r["name"]] = r
    ordered = sorted(frames.values(), key=lambda f: (f["clip"], f["frame"]))
    block["frames"] = ordered
    import collections
    c = collections.Counter(f["clip"] for f in ordered if f.get("status", "accepted") == "accepted")
    block["clip_totals"] = dict(sorted(c.items()))
    block["frame_count"] = len([f for f in ordered if f.get("status", "accepted") == "accepted"])
    CELLS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

def load_font(size=18):
    for p in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def make_sheet(names: list, out: Path) -> dict:
    data = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    by = {f["name"]: f for f in data[BLOCK]["frames"]}
    ok = [n for n in names if n in by and by[n]["status"] == "accepted"]
    z, cell = 2, CELL*2
    cols = min(8, max(1, len(ok)))
    rows = (len(ok)+cols-1)//cols
    sheet = Image.new("RGB", (cols*cell, rows*(cell+20)), (32,32,32))
    dr = ImageDraw.Draw(sheet); font = load_font(16)
    for i, n in enumerate(ok):
        im = Image.open(ROOT/by[n]["output"]).convert("RGBA").resize((cell, cell), Image.NEAREST)
        bg = Image.new("RGBA", (cell, cell), (40,40,40,255)); bg.alpha_composite(im)
        x, y = (i % cols)*cell, (i // cols)*(cell+20)
        sheet.paste(bg.convert("RGB"), (x, y))
        dr.text((x+4, y+cell+2), "%s h%d w%d"%(n, by[n]["height"], by[n]["width"]), fill=(230,230,230), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"path": rel(out), "frames": ok, "missing": [n for n in names if n not in ok]}

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("land"); p1.add_argument("--manifest", required=True)
    p2 = sub.add_parser("sheet"); p2.add_argument("--names", nargs="+", required=True); p2.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "land":
        mp = Path(a.manifest)
        entries = json.loads((mp if mp.is_absolute() else ROOT/mp).read_text(encoding="utf-8"))
        palette = load_palette()
        out_dir = ROOT/"art/fighters/ultraman-zero/stage1/cells"
        records = [land_one(e, palette, out_dir) for e in entries]
        merge_cells(records)
        print(json.dumps({
            "accepted": [r["name"] for r in records if r["status"] == "accepted"],
            "rejected": [{"name": r["name"], "rejects": r["rejects"], "gates": r["hard_gates"]} for r in records if r["status"] != "accepted"],
        }, ensure_ascii=False, indent=1))
        return 0 if all(r["status"] == "accepted" for r in records) else 1
    if a.cmd == "sheet":
        op = Path(a.out)
        print(json.dumps(make_sheet(a.names, op if op.is_absolute() else ROOT/op), ensure_ascii=False, indent=1))
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
