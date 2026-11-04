"""核验月亮三连保留16相、来源和已有测点；不重采样、不安装动作。"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/maintenance"))
from layout_runtime import translate
STAGE = ROOT / "art/fighters/ultraman-arc__luna/stage2"
CANDIDATES = STAGE / "light-chain-unregistered-20261102-v1"
SEEDS = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-complete16-offline-20261102-v1/measurement-seeds-v1.json"
TIMING = STAGE / "light-chain-whole-briefs-20261102-v1/timing-contract.json"
EXPECTED = {(action, phase) for action, count in (("light1", 5), ("light2", 5), ("light3", 6)) for phase in range(count)}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def checked(reference):
    path = (ROOT / translate(reference["path"])).resolve()
    path.relative_to(ROOT)
    if not path.is_file():
        raise ValueError(f"缺文件：{reference['path']}")
    data = path.read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        raise ValueError(f"LFS实体未下载：{path.relative_to(ROOT)}")
    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise ValueError(f"SHA256不符：{path.relative_to(ROOT)}")
    return path


def inspect():
    from PIL import Image
    import numpy as np
    errors, entries, seen = [], [], set()
    seeds = {(r["action"], r["phase"]): r for r in read(SEEDS)["phases"]}
    timing = {r["action"]: r for r in read(TIMING)["actions"]}
    for action, contract in timing.items():
        try:
            checked(contract["current_base_rule_reference_not_luna_install"])
        except (ValueError, OSError, KeyError) as error:
            errors.append(f"{action}时序依据已改变，须重新核对：{error}")
    for receipt_path in sorted(CANDIDATES.rglob("phase-receipt.json")):
        receipt = read(receipt_path)
        key = receipt["action"], receipt["phase"]
        if key not in EXPECTED or key in seen:
            errors.append(f"非预期或重复相：{key}")
            continue
        seen.add(key)
        row = {"action": key[0], "phase": key[1], "receipt": receipt_path.relative_to(ROOT).as_posix()}
        entries.append(row)
        try:
            sample_path = checked(receipt["whole_source_sample"])
            source_path = checked(receipt["source"])
            palette_path = checked(receipt["palette"])
            with Image.open(source_path) as image:
                if image.mode != "RGBA" or image.size != (1024, 1024):
                    raise ValueError("源不是1024整张RGBA")
            with Image.open(sample_path) as image:
                if image.mode != "RGBA" or image.size != (159, 159):
                    raise ValueError("候选不是159整张RGBA")
                pixels = np.asarray(image)
            alpha = pixels[:, :, 3]
            if set(np.unique(alpha)) != {0, 255} or np.any(pixels[alpha == 0]):
                raise ValueError("候选Alpha非二值或透明RGB未清零")
            if np.any(alpha[0]) or np.any(alpha[-1]) or np.any(alpha[:, 0]) or np.any(alpha[:, -1]):
                raise ValueError("候选人物接触整图边缘")
            palette = {tuple(c) for c in read(palette_path)["colors"]}
            if not {tuple(c) for c in pixels[alpha == 255, :3]} <= palette:
                raise ValueError("候选出现本人固定色板外颜色")
            seed = seeds[key]
            points = {code: bool(alpha[y, x] == 255) for code, (x, y) in seed["points"].items()}
            feet = {}
            for name, (x0, y0, x1, y1) in seed["feet"].items():
                yy, xx = np.where(alpha[y0:y1, x0:x1] == 255)
                if not len(yy):
                    raise ValueError(f"{name}鞋底ROI没有实体")
                feet[name] = int(yy.max()) + y0 + 1
            ground = feet[seed["support"]]
            run = next(r for r in timing[key[0]]["frame_runs"] if r["sprite"] == key[1])
            contact = None
            if seed["contact_roi"]:
                x0, y0, x1, y1 = seed["contact_roi"]
                entity = np.zeros(alpha.shape, dtype=bool)
                entity[y0:y1, x0:x1] = alpha[y0:y1, x0:x1] == 255
                hit = np.zeros(alpha.shape, dtype=bool)
                for x, y, width, height in run["hitboxes"]:
                    rx0, ry0, rx1, ry1 = 80+x, ground-y-height, 80+x+width, ground-y
                    hit[max(0, ry0):min(159, ry1), max(0, rx0):min(159, rx1)] = True
                contact = {"entity_pixels": int(entity.sum()), "original_rule_overlap_pixels": int((entity & hit).sum())}
            row.update(source=source_path.relative_to(ROOT).as_posix(), sample=sample_path.relative_to(ROOT).as_posix(),
                       sha256=receipt["whole_source_sample"]["sha256"], opaque_surface_points=points,
                       sole_boundaries=feet, support=seed["support"], proposed_whole_translation=[80, 280-ground],
                       ticks=run["ticks"], active=run["active"], contact=contact)
            if not all(points.values()):
                errors.append(f"{key}测点落在透明处，须目视复核")
            if bool(run["active"]) != (contact is not None):
                errors.append(f"{key}实体区与生效相不一致")
            if contact and not contact["original_rule_overlap_pixels"]:
                errors.append(f"{key}实体区未与原规则框相交")
        except (ValueError, OSError, KeyError) as error:
            row["error"] = str(error)
            errors.append(f"{key}: {error}")
    if seen != EXPECTED:
        errors.append(f"缺相：{sorted(EXPECTED-seen)}")
    verified = [row for row in entries if "error" not in row]
    if len(verified) == len(EXPECTED) and len({row["sha256"] for row in verified}) != len(EXPECTED):
        errors.append("16相候选存在重复像素文件，不能循环旧相冒充独立动作")
    return {"schema": "ufeneo.luna.light-chain-resume-check.v1", "phases": entries,
            "passed": not errors, "errors": errors, "installed": False, "playable": False,
            "visual_review_passed": False, "registration_accepted": False,
            "note": "只核保留实体和已有测点，不替代双向720/1080主游戏、实体命中与独立回放验收。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="可选，本机reports下的JSON结果")
    args = parser.parse_args()
    result = inspect()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        output = args.report.resolve()
        output.relative_to(ROOT / "reports")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
