"""仅盘月亮S2轻击三连既有整人源并出JPEG审片页；无生成、采样或运行安装。"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports/review/2026-11-02/luna-s2-light-chain-offline-review-v1"
BUNDLE = ROOT / "art/fighters/ultraman-arc__luna/stage2/goal-closeout-20261101-v1/bundle.json"
PROFILES = ROOT / "art/fighters/ultraman-arc__luna/stage2/ground-codex-20261027/profiles.json"
TIMING = ROOT / "art/fighters/ultraman-arc/stage4/ground/profiles.json"
ACTIONS = ["light1", "light2", "light3"]


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert sorted(path.name for path in OUT.iterdir()) == ["doctor.json"]
    bundle, profiles, timing = read(BUNDLE), read(PROFILES), read(TIMING)
    assert bundle["not_installed"] and bundle["transform_not_enabled"] and bundle["formal_playable_not_enabled"]
    rows, images, source_digests, summaries = [], {}, {}, []
    for action in ACTIONS:
        records = [row for row in bundle["frame_records"] if row["action"] == action]
        assert len(records) == profiles[action]["count"] == len(timing[action]["ticks"])
        for old in records:
            path = ROOT / old["source"]
            digest = sha(path)
            assert digest == old["source_sha256"]
            source_digests[path] = digest
            original = Image.open(path)
            image = original.convert("RGBA")
            images[(action, old["frame"])] = image
            alpha = np.asarray(image.getchannel("A"))
            solid = alpha >= 128
            coords = np.argwhere(solid)
            assert coords.size
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1
            border = np.concatenate([alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]])
            target = profiles[action]["targets"][old["frame"]]
            state_path = path.parent / "request-state.json"
            state = read(state_path) if state_path.is_file() else {}
            rows.append({
                "action": action, "frame": old["frame"], "source": rel(path), "source_sha256": digest,
                "source_mode": original.mode, "source_size": list(original.size),
                "alpha_min_max": [int(alpha.min()), int(alpha.max())],
                "alpha_zero_pixels": int((alpha == 0).sum()), "alpha_low_1_to_127_pixels": int(((alpha > 0) & (alpha < 128)).sum()),
                "alpha_128_to_254_pixels": int(((alpha >= 128) & (alpha < 255)).sum()),
                "alpha_255_pixels": int((alpha == 255).sum()),
                "solid_alpha128_bbox_exclusive": [int(x0), int(y0), int(x1), int(y1)],
                "all_alpha_bbox_exclusive": list(image.getbbox()),
                "solid_alpha128_touches_source_border": bool((border >= 128).any()),
                "all_alpha_touches_source_border": bool((border > 0).any()),
                "source_request_state_file": rel(state_path) if state_path.exists() else None,
                "source_request_state_sha256": sha(state_path) if state_path.exists() else None,
                "source_request_recorded_status": state.get("status"),
                "old_diagnostic_uniform_scale": old["prior_uniform_scale"],
                "old_diagnostic_reason": old["prior_scale_reason"],
                "old_diagnostic_not_shared_scale_approval": True,
                "old_diagnostic": old["prior_native"], "old_diagnostic_sha256": old["prior_native_sha256"],
                "old_whole_body_pack": old["image"], "old_whole_body_pack_sha256": old["image_sha256"],
                "timing_ticks": old["ticks"], "guide_description_not_measured": target["description"],
                "guide_facing": target["facing"], "guide_grounded": target["grounded"],
                "guide_points_not_measurements": True, "actual_visual_review_pending": True,
                "new_source_or_animation_generated": False, "installed": False,
            })
        selected = [row for row in rows if row["action"] == action]
        summaries.append({"action": action, "frames": len(records), "ticks": timing[action]["ticks"],
                          "all_selected_sources_have_distinct_byte_sha": len({row["source_sha256"] for row in selected}) == len(selected),
                          "old_diagnostic_scale_range": [min(row["old_diagnostic_uniform_scale"] for row in selected), max(row["old_diagnostic_uniform_scale"] for row in selected)],
                          "whole_source_sizes": sorted({tuple(row["source_size"]) for row in selected}),
                          "formal_main_review_exists_for_action": False})
    assert len(rows) == 16

    font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 14)
    smallfont = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 12)
    pages = []
    for action in ACTIONS:
        count = profiles[action]["count"]
        for theme, color, ink in [("dark", (24, 29, 38), (240, 243, 248)), ("light", (225, 227, 231), (24, 29, 38))]:
            for start in range(0, count, 4):
                selected = list(range(start, min(count, start + 4)))
                height = 56 + 402 * ((len(selected) + 1) // 2)
                page = Image.new("RGB", (768, height), color)
                draw = ImageDraw.Draw(page)
                draw.text((8, 3), f"月亮S2 {action} 既有完整源 · {theme} · art_source=existing", font=font, fill=ink)
                draw.text((8, 25), "整张源同比≤368；不裁人、不拼件、不作为最终采样或尺寸/动作签收", font=smallfont, fill=ink)
                binding = []
                for index, frame in enumerate(selected):
                    image = images[(action, frame)]
                    width, source_height = image.size
                    scale = min(368 / width, 368 / source_height)
                    size = [round(width * scale), round(source_height * scale)]
                    rgba = image.resize(size, Image.Resampling.LANCZOS)
                    x, y = 384 * (index % 2), 56 + 402 * (index // 2)
                    bg = Image.new("RGBA", size, color + (255,))
                    bg.alpha_composite(rgba)
                    page.paste(bg.convert("RGB"), (x + (384 - size[0]) // 2, y + 24))
                    row = next(item for item in rows if item["action"] == action and item["frame"] == frame)
                    draw.text((x + 8, y), f"{frame:02} / {width}×{source_height} / {row['timing_ticks']}tick / SHA {row['source_sha256'][:12]}", font=smallfont, fill=ink)
                    binding.append({"action": action, "frame": frame, "source": row["source"], "source_sha256": row["source_sha256"], "source_to_preview_scale": scale})
                output = OUT / f"{action}-{start:02}-full-source-{theme}.jpg"
                page.save(output, "JPEG", quality=80)
                assert output.stat().st_size <= 150 * 1024, output
                pages.append({"path": rel(output), "sha256": sha(output), "quality": 80, "size": list(page.size),
                              "bytes": output.stat().st_size, "theme": theme, "bindings": binding, "actual_view_pending": True})

    for path, digest in source_digests.items():
        assert sha(path) == digest
    save(OUT / "existing-source-inventory.json", {
        "schema": "ufeneo.arc-luna.s2.light-chain.existing-source-inventory.v1", "owner": "/root/luna_jump_resume",
        "art_source": "existing", "generation_route": "既有项目GPT Image完整帧原件；本轮没有发起生成",
        "next_unaccepted_action_in_original_ground_order": "light1", "action_group": ACTIONS,
        "basis_bundle": rel(BUNDLE), "basis_bundle_sha256": sha(BUNDLE),
        "guide_profiles": rel(PROFILES), "guide_profiles_sha256": sha(PROFILES),
        "timing_contract": rel(TIMING), "timing_contract_sha256": sha(TIMING),
        "actions": summaries, "sources": rows, "pages": pages,
        "old_sources_unchanged_after_review_render": True, "post_count": 0, "godot_executed": False,
        "product_or_old_art_mutated": False, "new_runtime_frames_or_clips": False,
        "strict_size_accepted": False, "action_motion_accepted": False, "formal_playable_enabled": False,
    })
    print(json.dumps({"report": rel(OUT / "existing-source-inventory.json"), "sha256": sha(OUT / "existing-source-inventory.json"), "actions": summaries, "review_pages": len(pages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
