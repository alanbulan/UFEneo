"""四角色专属特效家族安装：重着色图集 + phase3 条目 + 招式引用替换。

按家族清单一次装配一个角色：
  1. phase3_family_recolor 生成新图集（保留源形状与布局，只重映射色板）
  2. 写 provenance.json（源 SHA / 输出 SHA / 色板 / 方法）
  3. 从源 phase3 条目深拷贝字段，替换 texture/SHA/账本字段，插入新条目
  4. 递归替换该角色 moves/*.json 中的旧引用名

不碰招式数值、帧节奏与判定；旧条目与其它角色的引用不动。

用法：
  python tools/rebuild/<角色>/phase3_family_install.py            # 正式执行
  python tools/rebuild/<角色>/phase3_family_install.py --dry-run  # 只打印计划
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import hashlib
import json
from pathlib import Path
Path = _LayoutProjectPath

from phase3_family_recolor import recolor_atlas

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data, newline: bool) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text + ("\n" if newline else ""), encoding="utf-8", newline="\n")


def install(fighter: str, out_root_rel: str, families: list[dict], *, dry_run: bool = False) -> None:
    """families 每项:
    source   "ultraman-ace/metalium2_start"     源段目录（assets/effects 下）
    name     "mother_fx_slap_charge_start"      新条目名
    out      "slap_charge_start"                输出段目录（out_root 下）
    palette  ["#ffffff", ...]                   亮→暗关键色锚点
    refs     {"旧引用名": 1, ...}               本段需要替换的旧引用名（自检）
    """
    projectiles_path = ROOT / "content/presentation/phase3_projectiles.json"
    projectiles_raw = projectiles_path.read_text(encoding="utf-8")
    projectiles = json.loads(projectiles_raw)
    moves_dir = ROOT / f"content/fighters/{fighter}/moves"
    out_root = (ROOT / out_root_rel).resolve()
    src_root = (ROOT / "assets/effects").resolve()
    made: list[str] = []

    for fam in families:
        src_dir = src_root / fam["source"]
        out_dir = out_root / fam["out"]
        src_atlas = src_dir / "atlas.png"
        assert src_atlas.is_file(), f"源图集缺失: {src_atlas}"
        assert fam["name"] not in projectiles, f"条目已存在: {fam['name']}"
        src_entry = projectiles[fam["legacy"]]
        img, n_src, n_out = recolor_atlas(src_atlas, fam["palette"])
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            img.save(out_dir / "atlas.png")
            new_sha = sha(out_dir / "atlas.png")
            provenance = {
                "request": f"{fighter} 专属特效家族自制：保留源形状，按招式表光色重着色",
                "source": f"assets/effects/{fam['source']}/atlas.png",
                "source_sha256": sha(src_atlas),
                "output_sha256": new_sha,
                "source_entry": fam["legacy"],
                "method": "tools/rebuild/shared/phase3_family_recolor.py OKLab 亮度分层重着色",
                "target_palette": fam["palette"],
                "art_source": "recolor",
                "character_frames_modified": False,
                "review_status": "待指挥目视终审",
            }
            save_json(out_dir / "provenance.json", provenance, newline=True)
            entry = json.loads(json.dumps(src_entry, ensure_ascii=False))
            entry["texture"] = f"res://{out_root_rel}/{fam['out']}/atlas.png"
            entry["atlas_sha256"] = new_sha
            entry["provenance"] = f"res://{out_root_rel}/{fam['out']}/provenance.json"
            entry["art_source"] = "recolor"
            entry.pop("source", None)
            entry.pop("source_sha256", None)
            entry.pop("review", None)
            entry.pop("color_policy", None)
            if "colors" in entry:
                entry["colors"] = n_out
            if "dedicated_to" in entry:
                entry["dedicated_to"] = fighter
            else:
                entry["dedicated_to"] = fighter
            for key in ("user_approved", "art_approved"):
                if key in entry:
                    entry[key] = False
            if "review_status" in entry:
                entry["review_status"] = "2026-11-11 自制重着色，待指挥目视终审"
            projectiles[fam["name"]] = entry
            # 段目录 effect.json 与 phase3 条目保持 1:1（沿用 ultraman-jack 段目录先例）。
            save_json(out_dir / "effect.json", entry, newline=True)
        made.append(f"{fam['name']} <- {fam['legacy']} ({n_src}->{n_out}色)")

    # 招式引用替换。families 可带 "only_in": ["special3.json"]：refs 只在这些文件替换；
    # 带文件限定的先处理（同名的全局 family 靠顺序兜底），再全局替换其余。
    ref_map = {}
    scoped: list[tuple[dict, list[str]]] = []
    global_fams: list[dict] = []
    for fam in families:
        for old in fam["refs"]:
            if not fam.get("only_in") and old in ref_map and ref_map[old] != fam["name"]:
                raise SystemExit(f"引用映射冲突: {old} -> {ref_map[old]} / {fam['name']}")
            if not fam.get("only_in"):
                ref_map[old] = fam["name"]
        (scoped if fam.get("only_in") else global_fams).append(fam)

    def apply_replacements(paths, fam_list) -> dict[str, int]:
        out: dict[str, int] = {}
        for path in sorted(paths):
            active = [fam for fam in fam_list
                      if not fam.get("only_in") or path.name in fam["only_in"]]
            if not active:
                continue
            raw = path.read_text(encoding="utf-8")
            text = raw
            count = 0
            for fam in active:
                for old in sorted(fam["refs"], key=len, reverse=True):
                    token = f'"{old}"'
                    hits = text.count(token)
                    if hits:
                        text = text.replace(token, f'"{fam["name"]}"')
                        count += hits
            if count:
                out[path.name] = out.get(path.name, 0) + count
                if not dry_run:
                    data = json.loads(text)
                    assert json.dumps(data, ensure_ascii=False, indent=2) == text, f"{path.name} 往返不一致"
                    path.write_text(text, encoding="utf-8", newline="\n")
        return out

    replaced = apply_replacements(moves_dir.glob("*.json"), scoped)
    replaced.update(apply_replacements(moves_dir.glob("*.json"), global_fams))

    # 残留自检：本角色的 moves 不得再有本清单内旧引用
    if not dry_run:
        for path in sorted(moves_dir.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            for old in ref_map:
                assert f'"{old}"' not in text, f"{path.name} 残留 {old}"

    if not dry_run:
        save_json(projectiles_path, projectiles, newline=True)
    for line in made:
        print("  图集:", line)
    for name, count in sorted(replaced.items()):
        print(f"  引用: {name} ×{count}")
    print(f"  新条目 {len(families)} 个；替换 {sum(replaced.values())} 处引用"
          + ("（dry-run 未写盘）" if dry_run else ""))
