"""按已实看并签收的整图平移方案装配16相候选；不开放装甲。"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import check

ROOT = check.ROOT
OUTPUT = check.STAGE / "light-chain-registered-20261104-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def hurtboxes(image):
    alpha = np.asarray(image)[:, :, 3] == 255
    yy, _ = np.where(alpha)
    top, bottom = int(yy.min()), int(yy.max()) + 1
    boxes = []
    for band in range(3):
        y0, y1 = top + (bottom-top)*band//3, top + (bottom-top)*(band+1)//3
        _, xx = np.where(alpha[y0:y1])
        if len(xx):
            boxes.append([int(xx.min())-160, 280-y1, int(xx.max()-xx.min()+1), y1-y0])
    return boxes


def build(review_path):
    result = check.inspect()
    if not result["passed"]:
        raise ValueError("接续检查未过：" + "；".join(result["errors"]))
    review = check.read(review_path)
    if review.get("reviewer") != "root_delegated_by_user" or review.get("accepted_for_registration") is not True:
        raise ValueError("缺完整候选的实际目视及配准签收")
    approved = {(row["action"], row["phase"]): row for row in review["phases"]}
    if set(approved) != check.EXPECTED:
        raise ValueError("配准签收必须精确覆盖16相")
    if OUTPUT.exists():
        raise ValueError(f"候选位置已存在，不覆盖：{OUTPUT}")
    prepared = []
    for row in result["phases"]:
        decision = approved[(row["action"], row["phase"])]
        if decision["sample_sha256"] != row["sha256"] or decision["translation"] != row["proposed_whole_translation"]:
            raise ValueError("签收哈希或整图平移不符，须重新实看")
        sample = ROOT / row["sample"]
        with Image.open(sample) as image:
            full = Image.new("RGBA", (320, 320))
            full.paste(image, tuple(decision["translation"]))
        # 整159方平移，禁止裁剪、重采样和按身体部件修改。
        x, y = decision["translation"]
        if not (0 <= x and x+159 <= 320 and 0 <= y and y+159 <= 320):
            raise ValueError("完整159方超出注册画布")
        with Image.open(sample) as original:
            if full.crop((x, y, x+159, y+159)).tobytes() != original.tobytes():
                raise ValueError("注册没有保留整图像素")
        prepared.append((row, full))
    OUTPUT.mkdir(parents=True)
    actions = {}
    for action in ["light1", "light2", "light3"]:
        selected = sorted([(r, im) for r, im in prepared if r["action"] == action], key=lambda pair: pair[0]["phase"])
        atlas = Image.new("RGBA", (320*len(selected), 320))
        rows = []
        base_move_path = ROOT / f"content/fighters/ultraman-arc/moves/{action}.json"
        move = copy.deepcopy(check.read(base_move_path))
        for row, image in selected:
            image_path = OUTPUT / action / f"frame-{row['phase']:02}.png"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(image_path)
            atlas.paste(image, (row["phase"]*320, 0))
            boxes = hurtboxes(image)
            for frame in move["frames"]:
                if int(frame["sprite"]) == row["phase"]:
                    frame["hurtboxes"] = copy.deepcopy(boxes)
            rows.append({**row, "image": ref(image_path), "hurtboxes": boxes, "anchor": [160,280]})
        atlas_path = OUTPUT / action / "atlas.png"
        atlas.save(atlas_path)
        clip = {"texture": "res://" + atlas_path.relative_to(ROOT).as_posix(), "atlas_sha256": sha(atlas_path), "source_fighter": "ultraman-arc__luna",
                "cell": 320, "anchor_y": 280, "rects": [[i*320,0,320,320] for i in range(len(rows))], "ticks": [r["ticks"] for r in rows],
                "anchors": [[160,280] for _ in rows], "loop": False, "simulation_sprite_offset": 0}
        clip_path, move_path = OUTPUT / action / "clip.json", OUTPUT / action / "move.json"
        save(clip_path, clip)
        save(move_path, move)
        actions[action] = {"frames": rows, "clip": ref(clip_path), "move": ref(move_path), "rule_reference": ref(base_move_path)}
    manifest = {"schema": "ufeneo.luna.light-chain-registered-candidate.v1", "fighter": "ultraman-arc__luna",
                "registration_review": ref(review_path), "actions": actions, "source_scale": 159/1024,
                "processing_tools": {"register": ref(Path(__file__).resolve()), "check": ref(Path(check.__file__).resolve()), "measurements": ref(check.SEEDS)},
                "canvas": [320,320], "root": [160,280], "per_phase_rescale": False, "limb_editing": False,
                "rule_change": "只按本人整帧Alpha派生三带受击框；原攻击框、费用、伤害、取消及逐tick时序保持。",
                "installed": False, "playable": False, "main_game_accepted": False, "replay_accepted": False}
    manifest_path = OUTPUT / "manifest.json"
    save(manifest_path, manifest)
    return ref(manifest_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().review.resolve()), ensure_ascii=False))
