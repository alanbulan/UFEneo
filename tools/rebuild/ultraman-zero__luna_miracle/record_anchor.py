"""登记月神奇迹身份锚：cells.json 的锚/色板块与 requests.json 的照片门记录。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__luna_miracle"
FRAMES = ROOT / "art/fighters" / FIGHTER / "stage1/idle/frames"
CELLS = ROOT / "art/fighters" / FIGHTER / "stage1/cells/cells.json"
REQUESTS = ROOT / "art/fighters" / FIGHTER / "stage1/requests.json"
REPORT = ROOT / "tools/rebuild" / FIGHTER / "candidates-side/anchor-candidate-01.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    requests = json.loads(REQUESTS.read_text(encoding="utf-8"))
    native = FRAMES / "identity-idle-pixel.png"
    preview = FRAMES / "identity-idle-pixel-x4.png"
    source = FRAMES / "pixel-idle-source.png"
    source_src = ROOT / report["source"]
    if not source.exists():
        source.write_bytes(source_src.read_bytes())

    cells = {
        "fighter": FIGHTER,
        "cell": [256, 256],
        "anchor": [128, 248],
        "anchor_y": 248,
        "foot_row": 247,
        "target_standing_height": 188,
        "head_tolerance": 0.08,
        "standing_tolerance": 0.03,
        "palette": report["palette"],
        "palette_note": (
            "本批待机整帧重新定 32 色；旧图鉴缺黄眼/青绿额灯，不套用。"
            "眼黄 (241,226,2)、额灯青绿 (1,241,177)、胸计时器亮蓝 (0,143,253) 钉入色板。"
        ),
        "identity_anchor": {
            "path": rel(native),
            "sha256": sha256(native),
            "size": [256, 256],
            "native_bbox": report["bbox"],
            "standing_height": report["height"],
            "width": report["width"],
            "root": [128, 248],
            "foot_row": 247,
            "alpha_values": report["alpha_values"],
            "components": report["components"],
            "visible_colors": report["visible_colors"],
            "foot_outer_span": report["foot_outer_span"],
            "foot_span_over_height": report["foot_span_over_height"],
            "preview_x4": rel(preview),
            "preview_x4_sha256": sha256(preview),
            "production_reference": {
                "path": rel(source),
                "sha256": sha256(source),
                "note": "过照片门的像素整帧源；动作帧只引用本形态该帧，不追加其它角度或角色。",
            },
            "review_authority": "root_delegated_by_user",
            "user_approved": False,
            "date": "2026-11-12",
        },
        "frames": [
            {
                "frame": "idle-00",
                "source": rel(source),
                "source_sha256": sha256(source),
                "output": rel(native),
                "output_sha256": sha256(native),
                "scale": round(188 / report["sprite_size"][1], 8),
                "bbox": report["bbox"],
                "height": report["height"],
                "width": report["width"],
                "head_height": report["head_height_heuristic"],
                "head_ratio": report["head_ratio_heuristic"],
                "colors": report["visible_colors"],
                "components": report["components"],
                "foot_row": 247,
                "alpha": report["alpha_values"],
                "standing": True,
            }
        ],
        "notes": [
            "站高 188 与基础赛罗同档；256 制作格、根点 [128,248]、脚底 247。",
            "头高 54 为 stage_cells 启发式读数，仅报告；造型按原生格与 4× 目视核。",
            "站距 129/188=0.6862，在 0.65–0.80 内；两脚底差 1 px。",
        ],
    }
    CELLS.parent.mkdir(parents=True, exist_ok=True)
    CELLS.write_text(json.dumps(cells, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    side_batch = {
        "id": "side-batch-20261112",
        "purpose": "换侧视专用参考后一次多抽，选真实 90° 侧视格斗待机",
        "reference_images": [
            "art/fighters/ultraman-zero__luna_miracle/stage1/idle/references/luna-catalogue-side-x4.png",
            "art/fighters/ultraman-zero__luna_miracle/stage1/idle/references/luna-side-head-official.png",
            "art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png",
        ],
        "candidates": [
            {
                "id": "side-01",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-x-0-72-1100-20261112-124907.png",
                "sha256": "24c474d05dbbcbaa6a73155fab535d8f2a305dfabcbc65753885174f2ffb7590",
                "size": [1199, 1312],
                "bbox": [197, 65, 974, 1248],
                "foot_span_over_height": 0.6562,
                "foot_bottom_delta": 1,
                "status": "candidate_rejected",
                "reason": "站距达标但躯干偏薄、后腿接近伸直，屈膝下沉不足；作为备选未选。",
            },
            {
                "id": "side-02",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-70-1100-20261112-125126.png",
                "sha256": "c195a6f1bbccd3cfac9212c8b23d9b1ecec7cba16ca9bd29f374411eb47b68cb",
                "size": [1193, 1318],
                "bbox": [210, 63, 952, 1269],
                "foot_span_over_height": 0.6147,
                "foot_bottom_delta": 4,
                "status": "rejected",
                "reason": "站距 0.6147 低于 0.65 下限。",
            },
            {
                "id": "side-03",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-68-1100-20261112-125236.png",
                "sha256": "9c4581d3281907acc9eef24c5a8a255a3d8428ec3281c98c25d2a7fdfd72a936",
                "size": [1181, 1331],
                "bbox": [164, 49, 995, 1266],
                "foot_span_over_height": 0.6823,
                "foot_bottom_delta": 17,
                "status": "candidate_rejected",
                "reason": "站距达标但两脚底差 17 px、后脚离地，接地不稳；未选。",
            },
            {
                "id": "side-04",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-70-1100-20261112-125354.png",
                "sha256": "c5f7525e4a90735b28002c9b09ba1858eb168879fc0a4033b7a8380ecd68d378",
                "size": [1199, 1312],
                "bbox": [240, 76, 945, 1249],
                "foot_span_over_height": 0.6005,
                "foot_bottom_delta": 3,
                "status": "rejected",
                "reason": "站距 0.6005 低于 0.65 下限。",
            },
            {
                "id": "side-05",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-68-1100-20261112-125529.png",
                "sha256": "b5027d84174d956fe0e53cc783c5d56a53fa3bf59a2ee0b328ede987595a9823",
                "size": [1254, 1254],
                "bbox": [241, 127, 986, 1160],
                "foot_span_over_height": 0.7205,
                "foot_bottom_delta": 2,
                "status": "selected",
                "reason": (
                    "纯右侧视、只见一侧肩胸；站距 0.7205；两脚底差 2 px；双膝屈、髋下沉、"
                    "双拳胸前护架；双蓝冠鳍根在额侧、向后上掠、尖端在后脑上方；银冠脊、"
                    "青绿额灯、黄眼、银层叠胸肩甲、蓝胸计时器、蓝四肢白纹齐全。"
                ),
            },
            {
                "id": "side-06",
                "path": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-70-1100-20261112-125626.png",
                "sha256": "005f2f8b9d3cb07ca79adf3cf450cca829f614f20f955c1d65275c90b4bba39a",
                "size": [1208, 1302],
                "bbox": [288, 64, 871, 1237],
                "foot_span_over_height": 0.4966,
                "foot_bottom_delta": 1,
                "status": "rejected",
                "reason": "站距 0.4966 明显低于下限，双腿收窄。",
            },
        ],
        "selected": "side-05",
        "cleaning": {
            "tool": "tools/rebuild/ultraman-zero__luna_miracle/clean_candidate.py",
            "note": "只删除与主体断开的漂浮颗粒，人物像素未改。",
            "source": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/90-0-68-1100-20261112-125529.png",
            "source_sha256": "b5027d84174d956fe0e53cc783c5d56a53fa3bf59a2ee0b328ede987595a9823",
            "cleaned": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/references/stance-side-approved.png",
            "cleaned_sha256": "71bb6ae331ac3e86acd006a6c63e39b4434a86426f7bd16a0cd1e163fa53db78",
            "components_before": 3472,
            "removed_pixels": 31554,
        },
        "pixel_idle": {
            "raw": "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/2d-90-20261112-130025.png",
            "raw_sha256": "f544cc4e9887dd960480820717c3675428aa2b538420c328e7020fc9b04e4339",
            "raw_size": [1254, 1254],
            "cleaned": "tools/rebuild/ultraman-zero__luna_miracle/candidates-side/2d-90-clean.png",
            "cleaned_sha256": "41aa0c5787108812295ccd2b4fa50cd4feceaac53c9d6bb1c6239cce52d8ae1e",
            "prompt": (
                "把参考图的格斗待机姿势原样转成 2D 像素整帧，不重新设计造型。固定右侧视90°，"
                "只见一侧肩胸；站距、前后脚屈膝下沉、双拳胸前护架照参考；双蓝冠鳍根在额侧太阳穴"
                "上方、贴头壳向后上掠、尖端在后脑上方；银冠脊、青绿额灯、黄眼、银层叠胸肩甲、"
                "蓝胸计时器、蓝四肢与白/银纹全部照参考。像素块清晰、色块平整，无渐变无抗锯齿；"
                "四肢粗细、头肩比例和体量与参考完全一致，不增肌、不缩头。完整不裁切，四周留白，"
                "透明背景，只有人物本体，无地面文字边框特效、无漂浮颗粒。"
            ),
            "reference_images": [
                "art/fighters/ultraman-zero__luna_miracle/stage1/idle/references/stance-side-approved.png"
            ],
            "generation_id": "image-3954-1255",
            "cleaned_metrics": {
                "bbox": [242, 113, 978, 1171],
                "height": 1059,
                "foot_outer_span": 736,
                "foot_span_over_height": 0.695,
                "foot_bottom_delta": 10,
            },
        },
    }
    requests["side_view_batch_2026_11_12"] = side_batch
    requests["identity_anchor_for_actions"] = {
        "path": rel(native),
        "sha256": sha256(native),
        "size": [256, 256],
        "native_bbox": report["bbox"],
        "standing_height": 188,
        "root": [128, 248],
        "foot_row": 247,
        "preview_x4": rel(preview),
        "preview_x4_sha256": sha256(preview),
        "production_reference": {
            "path": rel(source),
            "sha256": sha256(source),
            "note": "动作帧唯一参考为本形态该像素整帧；不追加其它角度或角色。",
        },
        "palette": report["palette"],
        "review_authority": "root_delegated_by_user",
        "user_approved": False,
        "date": "2026-11-12",
    }
    requests["stop"]["decision"] = (
        "旧三帧 3/4 停止后已换侧视专用参考，side-05 通过照片门并转像素锚；"
        "像素锚按 root_delegated_by_user 签收（不是用户亲审）。"
    )
    requests["stop"]["resolved_by"] = "side-batch-20261112"
    REQUESTS.write_text(json.dumps(requests, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(json.dumps({"cells": rel(CELLS), "requests": rel(REQUESTS),
                      "anchor_sha256": sha256(native),
                      "source": rel(source), "source_sha256": sha256(source)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
