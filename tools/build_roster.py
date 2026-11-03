"""Compile the editable roster and first-party evidence into Godot content packs."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from collections import Counter
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import json; json = _LayoutJson
import re
import unicodedata
import wiki_catalog
from art_paths import brief_path

ROOT = _LayoutProjectPath(_layout_root)
DATA = ROOT / "content/roster"
FUSIONS = {
    "ultraman-legend": ["ultraman-cosmos", "ultraman-justice"],
    "ultraman-saga": ["ultraman-zero", "ultraman-dyna", "ultraman-cosmos"],
    "ultraman-ginga-victory": ["ultraman-ginga", "ultraman-victory"],
    "ultraman-ruebe": ["ultraman-rosso", "ultraman-blu"],
    "ultraman-groob": ["ultraman-rosso", "ultraman-blu", "ultrawoman-grigio"],
    "ultraman-reiga": ["ultraman-ginga", "ultraman-victory", "ultraman-x", "ultraman-orb", "ultraman-geed",
                      "ultraman-rosso", "ultraman-blu", "ultrawoman-grigio", "ultraman-taiga", "ultraman-titas", "ultraman-fuma"],
}
WORKS = {
    "ultraman": "ultraman", "ultraseven": "seven", "return_of_ultraman": "jack", "ultraman_ace": "ace",
    "ultraman_taro": "taro", "ultraman_leo": "leo", "ultraman_80": "80", "ultraman_tiga": "tiga",
    "ultraman_dyna": "dyna", "ultraman_gaia": "gaia", "ultraman_cosmos": "cosmos",
    "ultraman_nexus": "nexus", "ultraman_max": "max", "ultraman_mebius": "mebius",
    "ultraman-arc": "arc", "ultraman-omega": "omega", "ultraman-teo": "teo", "ultraman-blazar": "blazar",
    "ultraman_decker": "decker", "ultraman_trigger_new_generation_tiga": "trigger", "ultraman_z": "z",
}
APPEARANCES = {
    "mebius": ["ultraman", "ultraseven", "ultraman-jack", "ultraman-ace", "ultraman-taro", "ultraman-leo", "ultraman-80", "zoffy"],
    "zero": ["ultraman", "ultraseven", "ultraman-mebius", "gomora"],
    "saga": ["ultraman-zero", "ultraman-dyna", "ultraman-cosmos"],
    "geed": ["ultraman-zero", "ultraman_belial"], "taiga": ["ultraman-tregear", "ultraman-taro"],
    "z": ["ultraman-zero", "ultraman-geed", "jugglus_juggler", "windom"],
    "trigger": ["ultraman-z"], "decker": ["ultraman-trigger", "carmeara"],
    "regulos": ["ultraman-regulos", "ultraman-ribut", "alien_magmas"],
    "teo": ["ultraman-zero"],
}
STAGES = ["identity_research", "base_concept", "pixel_grid_review", "idle_anchor", "action_rows", "motion_qa", "combat_implementation", "balance", "runtime_release"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).lower()


def make_catalog(seed, sources):
    heroes = {}
    cards = []
    for source in sources["sources"]:
        for entry in source["entries"]:
            if source["id"] == "global-heroes":
                heroes[entry["url"].rstrip("/").split("/")[-1]] = (source["id"], entry)
            elif source["id"].startswith("jp-kaiju"):
                cards.append((source["id"], entry))
    entries = {}
    series = []

    def add(raw, kind, work):
        bits = raw.split("|")
        cid, name = bits[:2]
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", cid), cid
        if cid in entries:
            if work["id"] not in entries[cid]["series_ids"]:
                entries[cid]["series_ids"].append(work["id"])
            return entries[cid]
        row = {"id": cid, "name": name, "kind": kind, "era": work["era"], "series_ids": [work["id"]],
               "catalog_year": work["year"], "aliases": bits[2:], "base_character": "", "fusion_components": FUSIONS.get(cid, []),
               "identity_evidence": "research_pending", "association_evidence": "planning_pending_episode_check",
               "sources": [], "official_url": "", "playable": False, "fighter_resource": "",
               "production_stage": "identity_research", "brief": brief_path(cid, kind)}
        if cid in heroes:
            sid, evidence = heroes[cid]
            row.update(identity_evidence="official_index", sources=[sid], official_url=evidence["url"])
            row["aliases"].append(evidence["name"])
        if kind == "story" and work["id"] == "teo":
            row.update(identity_evidence="official_series", association_evidence="official_series", sources=["teo-series"], official_url="https://m-78.jp/teo/")
        for sid, evidence in cards:
            if WORKS.get(evidence["work"]) == work["id"] and any(norm(evidence["name"]).endswith(norm(a)) for a in bits[2:]):
                row.update(identity_evidence="official_work_directory", association_evidence="official_work_directory", sources=[sid], official_url=evidence["url"])
                break
        entries[cid] = row
        return row

    for work in seed["series"]:
        series.append({k: work[k] for k in ["id", "name", "year", "era"]})
        for group, kind in [("heroes", "hero"), ("foes", "kaiju"), ("humans", "story")]:
            for raw in work[group]:
                add(raw, kind, work)
        for parent, forms in work.get("forms", {}).items():
            for raw in forms:
                suffix, label = raw.split("|")
                row = add(parent + "__" + suffix + "|" + entries[parent]["name"] + " · " + label, "form", work)
                row["base_character"] = parent
                row["form_kind"] = "suit_variant" if parent == "ultraman" else "combat_form_to_research"
    # Import every unique card actually observed for a supported work. Do not invent translations.
    for sid, evidence in cards:
        wid = WORKS.get(evidence["work"])
        if not wid:
            continue
        if '一覧へ' in evidence['name']:
            continue
        if any(row["official_url"] == evidence["url"] for row in entries.values()):
            continue
        work = next(x for x in seed["series"] if x["id"] == wid)
        slug = evidence["url"].rstrip("/").split("/")[-1]
        cid = "kaiju_" + slug.replace("-", "_")
        row = add(cid + "|" + evidence["name"], "kaiju", work)
        row.update(identity_evidence="official_work_directory", association_evidence="official_work_directory", sources=[sid], official_url=evidence["url"])
        row["name_note"] = "官方日文名；中文译名待核"
    for wid, ids in APPEARANCES.items():
        for cid in ids:
            if wid not in entries[cid]["series_ids"]:
                entries[cid]["series_ids"].append(wid)
    for child, parent in {"arc_belial": "ultraman_belial", "belial_atrocious": "ultraman_belial"}.items():
        entries[child]["kind"] = "form"
        entries[child]["base_character"] = parent
        entries[child]["form_kind"] = "combat_form_to_research"
    for cid in ["ultraman_belial", "ultraman-tregear", "dark_zagi", "dark_mephisto", "dark_faust", "evil_tiga", "camearra", "darramb", "hudra", "carmeara", "darrgon", "hudram", "evil_trigger", "ultraman_shadow", "ultraman_orb_dark", "chaos_ultraman"]:
        entries[cid]["kind"] = "dark_ultra"
    for cid in ["pigmon", "windom", "miclas", "aguila", "sevenger", "earth_garon", "king_joe_storage", "emi"]:
        entries[cid]["alignment_note"] = "友方或支援角色；不按反派处理"
    wiki_index = ROOT / "docs/research/wikipedia/index.json"
    if wiki_index.exists():
        wiki = load(wiki_index)["pages"]
        for cid, (name, wid, note) in load(DATA / "name-overrides.json")["names"].items():
            if cid not in entries:
                continue
            row = entries[cid]
            row["aliases"].append(row["name"])
            row["name"] = name
            row["name_note"] = note
            source = next((s for s in wiki if s["id"] == "series_" + wid), None)
            if source:
                row["name_source"] = source["revision_url"]
        extracted_path = DATA / "wiki-extracted.json"
        if extracted_path.exists():
            wiki_catalog.merge(entries, series, load(extracted_path), wiki)
        for row in entries.values():
            row["wikipedia"] = [x for x in wiki if x["status"] == "fetched" and
                                (x["id"] == "character_" + row["id"] or
                                 x["id"] in {n["source"] for n in row.get("research_notes", [])} or
                                 (not x["id"].startswith("master_") and any(sid in x.get("targets", []) for sid in row["series_ids"])))]
            note_sources = {n["source"] for n in row.get("research_notes", []) if n["text"]}
            row["wikipedia"].sort(key=lambda x: 9 if x["language"] != "zh" else
                                  0 if x["id"] == "character_zh_" + row["id"] else
                                  1 if x["id"] in note_sources else
                                  2 if x["id"] == "series_" + row["series_ids"][0] else 4)
        for work in seed["series"]:
            if not work["heroes"]:
                continue
            primary = entries[work["heroes"][0].split("|")[0]]
            for source in wiki:
                if source["id"] == "series_" + work["id"] and source["status"] == "fetched" and source["title"] not in primary["aliases"]:
                    primary["aliases"].append(source["title"])
    # Resolve after classification/merging, since evidence may change a row's kind.
    for row in entries.values():
        row["brief"] = brief_path(row["id"], row["kind"])
    # This grouping year describes the work's start, not each character's precise debut date.
    return {"schema": 1, "research_date": "2026-10-19", "scope": seed["scope"],
            "year_semantics": "所属作品分组首年；不等于每名角色/形态的首次登场年份",
            "series": series, "entries": sorted(entries.values(), key=lambda x: (x["catalog_year"], x["kind"], x["id"]))}


def draft_brief(row):
    return {"character_id": row["id"], "managed_by": "tools/build_roster.py", "asset_kind": "character", "model": "gpt-image-2.5-sunburst", "size": "1024x1024", "quality": "low",
            "ready_for_generation": False, "layer_contract": "art/shared/specs/fighter-layer-contract.json", "target_logical_cell": [192, 192], "required_references": ["reviewed_official_identity_reference"],
            "identity_source": row["official_url"], "identity_checklist": ["核对作品版本、脸部、轮廓、配色、装备与变身形态", "人物正侧背资料与必杀姿势", "不使用换色占位体冒充角色"],
            "research_documents": [x["file"] for x in row.get("wikipedia", [])],
            "prompt": "DRAFT — requires reviewed identity reference before generation. Create " + row["name"] + " (" + row["id"] + "). " +
            ("Single story portrait, original stylized pixel illustration, no actor likeness assumed. " if row["kind"] == "story" else "One full-body combat idle pose facing right, feet and all appendages visible; match the reviewed identity reference exactly. ") +
            "True hard pixel blocks, shared arcade fighting-game style, restrained palette, no anti-aliasing, gradients, text, logos, effects or cast shadow. 透明背景，真正的 PNG Alpha 透明通道；不要纯色底、棋盘格、地面或投影。 Candidate only; not approved runtime animation."}


def outputs(catalog):
    combat = load(ROOT / "content/combat/neo.json")
    result = {DATA / "catalog.json": catalog}
    summaries = []
    for row in catalog["entries"]:
        detail = DATA / "details" / (row["id"] + ".json")
        result[detail] = row
        summary = {key: row[key] for key in ["id", "name", "kind", "era", "series_ids", "catalog_year", "base_character", "playable", "fighter_resource"]}
        summary["search_text"] = (row["name"] + " " + row["id"] + " " + " ".join(row["aliases"])).lower()
        summary["detail_path"] = detail.relative_to(ROOT).as_posix()
        summaries.append(summary)
    # The game opens this compact index, never the complete research catalog.
    result[DATA / "index.json"] = {"schema": 1, "purpose": "轻量检索索引；详细资料按角色读取",
                                    "series": catalog["series"], "entries": summaries}
    for row in catalog["entries"]:
        path = DATA / "packs" / (row["id"] + ".json")
        result[path] = {"schema": 1, "character_id": row["id"], "catalog": "content/roster/catalog.json",
                        "role": row["kind"], "base_character": row["base_character"],
                        "production_stages": ["identity_research", "portrait", "story_script", "dialogue_qa", "story_release"] if row["kind"] == "story" else STAGES,
                        "research_documents": [x["file"] for x in row.get("wikipedia", [])],
                        "skill_and_form_candidates": "docs/research/wikipedia/term-index.json",
                        "deliverables": ["portrait"] if row["kind"] == "story" else combat["required_animations"],
                        "combat_notes": {} if row["kind"] == "story" else {"neo": combat["production_notes"], "source": "content/combat/neo.json"},
                        "asset_layer_contract": combat["asset_layers"],
                        "release_gate": "剧情头像与文本验收；不注册为格斗角色" if row["kind"] == "story" else "身份、像素网格、动作原点、帧时长、判定及新纪元组合输入测试均通过后才注册为可玩角色"}
        brief = ROOT / row["brief"]
        existing = load(brief) if brief.exists() else {}
        if not brief.exists() or (existing.get("managed_by") == "tools/build_roster.py" and not existing.get("ready_for_generation")):
            result[brief] = draft_brief(row)
    extracted_path = DATA / "wiki-extracted.json"
    episodes = load(extracted_path)["episodes"] if extracted_path.exists() else []
    extracted = load(extracted_path) if extracted_path.exists() else {"unresolved":[], "entities":[]}
    coverage = {"schema":1, "complete":False, "scope":"已抓取的维基作品页、角色列表、英雄总表及怪兽表",
                "records":len(catalog["entries"]), "extracted_records":len(extracted["entities"]),
                "unresolved_source_records":len(extracted["unresolved"]), "episode_research_rows":len(episodes),
                "known_gaps":["尚未穷尽所有电影、外传、漫画、舞台剧、游戏原创内容", "日文专名及同名个体仍需继续核对", "自动抽取的形态和出场关系需要资料复核", "播映表研究记录尚未编写成可运行剧情关卡"], "works":[]}
    for work in catalog["series"]:
        members = [x for x in catalog["entries"] if work["id"] in x["series_ids"]]
        coverage["works"].append({"id":work["id"], "name":work["name"], "kinds":dict(Counter(x["kind"] for x in members)),
                                  "episode_rows":sum(work["id"] in ep["series_ids"] for ep in episodes),
                                  "complete":False})
        result[DATA / "campaigns" / (work["id"] + ".json")] = {
            "schema": 1, "id": work["id"], "name": work["name"], "year": work["year"], "status": "story_research",
            "character_pools": {kind: [x["id"] for x in members if x["kind"] == kind] for kind in sorted({x["kind"] for x in members})},
            "research_documents": sorted({source["file"] for x in members for source in x.get("wikipedia", []) if work["id"] in source.get("targets", [])}),
            "episodes": [], "research_episodes": [ep for ep in episodes if work["id"] in ep["series_ids"]],
            "episode_contract": ["title", "characters", "objectives", "event_triggers", "special_win_or_loss", "rating", "rewards", "unlocks", "evidence"]}
    result[DATA / "coverage.json"] = coverage
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = make_catalog(load(DATA / "series.json"), load(DATA / "sources.json"))
    stale = []
    for path, data in outputs(catalog).items():
        text = (json.dumps(data, ensure_ascii=False, separators=(",", ":")) if path.name == "index.json" else json.dumps(data, ensure_ascii=False, indent=2)) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if stale:
        raise SystemExit("Stale roster output: " + ", ".join(stale[:10]))
    print(json.dumps({"series": len(catalog["series"]), "entries": len(catalog["entries"]), "kinds": Counter(x["kind"] for x in catalog["entries"]),
                      "official_identity_evidence": sum(x["identity_evidence"].startswith("official_") for x in catalog["entries"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
