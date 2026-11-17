"""把名册名称拆成三项：称号 / 主体名称 / 形态。

用户反馈：不少条目把称号当成名字，名字与形态挤在一个字段里，还因此产生重复。
本工具做确定性的拆分与去重提案，输出报告；加 --apply 才写回。

拆分规则（按优先级）：
1. identity_display.json 已有 title 的，称号以它为准（人工核实过的来源）。
2. 名称里的 " · " 右侧一律是形态。
3. 结尾的中文括注（维基译名/独立世界观等）移到 note，不算名字。
4. 名称里夹着 "<称号><名字>" 的，按类别词切开；只对怪兽/宇宙人/黑暗巨人/
   形态生效，剧情人物不拆（"宗像龙彦"不是称号+名字）。
5. 形态类条目若名称里没有分隔符，保留空形态并列入报告等人工判断。
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROSTER = ROOT / "content/roster"
REPORT = ROOT / "reports/roster/identity-fields.json"

FORM_SEPARATOR = " · "
PAREN_TAIL = re.compile(r"\s*[（(]([^（）()]*)[）)]\s*$")
# 类别词按长度降序匹配，避免"暴龙"先被"龙"吃掉。
CATEGORY = re.compile(
    r"^(?P<epithet>.{2,8}?(?:"
    r"宇宙甲壳怪兽|超时空魔神|宇宙钢铁龙|破坏暗暴龙|破坏暴龙|机械守护兽|爆进细胞怪兽"
    r"|怪兽|魔兽|凶兽|幻兽|神兽|圣兽|妖兽|灵兽|甲兽|铁兽|钢兽|冥兽|炎兽|冰兽|岩兽"
    r"|沙兽|水兽|风兽|雷兽|光兽|暗兽|守护兽|暴龙|恐龙|怪鸟|怪鱼|怪虫|怪植物|怪人"
    r"|机器人|机械兽|宇宙人|海兽|地兽|空兽|超兽|两栖兽|甲壳兽|软体兽|植物兽|昆虫兽"
    r"))\s*(?P<name>[一-鿿·A-Za-z0-9]{2,})$"
)
SPLIT_KINDS = {"kaiju", "hero", "dark_ultra", "form"}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def split_name(raw: str, kind: str, known_title: str) -> dict:
    """返回 {title, name, form, note, rule}；不改动原文。"""
    text = raw.strip()
    note = ""
    found = PAREN_TAIL.search(text)
    if found and len(found.group(1)) <= 12:
        note = found.group(1).strip()
        text = PAREN_TAIL.sub("", text).strip()
    form = ""
    if FORM_SEPARATOR in text:
        head, _, tail = text.partition(FORM_SEPARATOR)
        text, form = head.strip(), tail.strip()
    epithet = ""
    # 已有称号直接是名称前缀时（"高原龙希多拉" / "古代怪兽 里奥德"）先剪掉，
    # 否则称号会在名字里留一份副本。
    if known_title and text.startswith(known_title) and len(text) > len(known_title) + 1:
        text = text[len(known_title):].strip()
    if not text and known_title:
        text, known_title = known_title, ""
    if not known_title and kind in SPLIT_KINDS:
        found = CATEGORY.match(text)
        if found:
            epithet = found.group("epithet")
            text = found.group("name").strip()
    title = known_title or epithet
    rule = "identity_title" if known_title else ("epithet_split" if epithet else ("form_split" if form else "plain"))
    return {"title": title, "name": text, "form": form, "note": note, "rule": rule}


def duplicate_groups(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[str]] = defaultdict(list)
    for row in rows:
        key = (str(row.get("name", "")).strip(), str(row.get("form", "")).strip().lower())
        if key[0]:
            groups[key].append(str(row["id"]))
    return [{"name": key[0], "form": key[1], "ids": ids}
            for key, ids in sorted(groups.items()) if len(ids) > 1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="写回 catalog/index/details/identity_display")
    parser.add_argument("--report", default=str(REPORT))
    args = parser.parse_args()

    identity = read(ROSTER / "identity_display.json")
    identity_entries = identity.setdefault("entries", {})
    catalog = read(ROSTER / "catalog.json")
    rows = catalog["entries"]
    index = read(ROSTER / "index.json")
    index_by_id = {str(row["id"]): row for row in index["entries"]}

    changes, unresolved = [], []
    for row in rows:
        cid = str(row["id"])
        # 称号优先级：人工核实过的 identity_display > 名册原有 title > 名称里的类别词。
        known_title = str(identity_entries.get(cid, {}).get("title", "")).strip()
        if not known_title:
            known_title = str(row.get("title", "")).strip()
        parts = split_name(str(row["name"]), str(row.get("kind", "")), known_title)
        before = (row.get("name"), row.get("title", ""), row.get("form", ""))
        after = (parts["name"], parts["title"], parts["form"])
        if before != after:
            changes.append({"id": cid, "before": list(before), "after": list(after),
                            "rule": parts["rule"], "note": parts["note"]})
        row["title"] = parts["title"]
        row["name"] = parts["name"]
        row["form"] = parts["form"]
        if parts["note"]:
            row["name_note"] = parts["note"]
        detail = ROSTER / "details" / (cid + ".json")
        if args.apply and detail.is_file():
            data = read(detail)
            data["title"], data["name"], data["form"] = parts["title"], parts["name"], parts["form"]
            if parts["note"]:
                data["name_note"] = parts["note"]
            write(detail, data)
        summary = index_by_id.get(cid)
        if summary is not None:
            summary["name"] = parts["name"]
            summary["title"] = parts["title"]
            summary["form"] = parts["form"]
            summary["search_text"] = " ".join(x for x in [
                parts["title"], parts["name"], parts["form"], cid,
                " ".join(str(a) for a in row.get("aliases", [])),
            ] if x).lower()
        if row.get("kind") == "form" and not parts["form"]:
            unresolved.append({"id": cid, "name": parts["name"], "base": row.get("base_character", "")})

    for entry_id, entry in identity_entries.items():
        row = next((r for r in rows if str(r["id"]) == str(entry_id)), None)
        if row is not None and row.get("title") and not str(entry.get("title", "")).strip():
            entry["title"] = row["title"]

    duplicates = duplicate_groups(rows)
    covered = sum(1 for r in rows if str(r.get("title", "")).strip())
    report = {
        "schema": 1,
        "purpose": "称号/主体名称/形态三分结果；含重复组与待判断形态。",
        "total": len(rows),
        "with_title": covered,
        "without_title": len(rows) - covered,
        "changed": len(changes),
        "changes": changes,
        "duplicates": duplicates,
        "form_without_form": unresolved,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write(report_path, report)

    if args.apply:
        write(ROSTER / "catalog.json", catalog)
        write(ROSTER / "index.json", index)
        write(ROSTER / "identity_display.json", identity)
        for cid in [str(r["id"]) for r in rows]:
            detail = ROSTER / "details" / (cid + ".json")
            if not detail.is_file():
                continue
    print(json.dumps({"total": len(rows), "with_title": covered, "changed": len(changes),
                      "duplicates": len(duplicates), "form_without_form": len(unresolved),
                      "applied": args.apply}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
