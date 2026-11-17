"""为图鉴缺图条目补充日文/英文别名，便于按作品检索官方参考图。

数据来源：仓库内的 wiki 抽取结果、roster details 的 aliases、以及
catalogue_display 的 search_text。只做确定性整理，不联网。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KANA = re.compile(r"[゠-ヿｦ-ﾟ]")
LATIN = re.compile(r"[A-Za-z]{3,}")
CJK = re.compile(r"[一-鿿]")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_aliases(row: dict) -> list[str]:
    """从 details、display、wiki 抽取所有已知名称。"""
    names: list[str] = []
    seen: set[str] = set()

    def push(value: object) -> None:
        if not isinstance(value, str):
            return
        text = value.strip()
        if text and text not in seen:
            seen.add(text)
            names.append(text)

    push(row.get("name"))
    detail_path = ROOT / str(row.get("detail_path", ""))
    if detail_path.is_file():
        detail = load(detail_path)
        for alias in detail.get("aliases") or []:
            push(alias)
        push(detail.get("original"))
    for alias in row.get("aliases") or []:
        push(alias)
    for token in str(row.get("search_text", "")).split():
        # wiki_xxxx 是内部 id，不是可检索的名字。
        if token.startswith("wiki_"):
            continue
        push(token)
    return names


def classify(names: list[str]) -> dict:
    japanese = [n for n in names if KANA.search(n)]
    english = [n for n in names if LATIN.search(n) and not KANA.search(n)]
    chinese = [n for n in names if CJK.search(n)]
    return {
        "japanese": japanese,
        "english": english,
        "chinese": chinese,
        "has_japanese": bool(japanese),
        "has_english": bool(english),
    }


def wiki_lookup(row: dict, wiki_entities: list[dict]) -> list[str]:
    """在 wiki 抽取结果里按中文名/别名找对应实体，取它的 original 与 aliases。"""
    wanted = {n for n in collect_aliases(row) if CJK.search(n)}
    found: list[str] = []
    for entity in wiki_entities:
        pool = [entity.get("name", ""), entity.get("original", "")] + list(entity.get("aliases") or [])
        if any(w in wanted for w in pool if w):
            for value in pool:
                if value and value not in found:
                    found.append(value)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/catalogue-ref/_retry")
    args = parser.parse_args()

    index = load(ROOT / "content/roster/index.json")
    display = load(ROOT / "content/roster/catalogue_display.json")
    wiki = load(ROOT / "content/roster/wiki-extracted.json").get("entities", [])
    have_image = display.get("entries", {})

    pending = [
        row for row in index["entries"]
        if not have_image.get(row["id"], {}).get("image")
    ]

    args.out.mkdir(parents=True, exist_ok=True)
    stats = {"total": 0, "with_japanese": 0, "with_english": 0, "recovered": 0}
    for row in pending:
        names = collect_aliases(row)
        before = classify(names)
        if not before["has_japanese"]:
            extra = wiki_lookup(row, wiki)
            for value in extra:
                if value not in names:
                    names.append(value)
        after = classify(names)
        if not before["has_japanese"] and after["has_japanese"]:
            stats["recovered"] += 1
        stats["total"] += 1
        stats["with_japanese"] += after["has_japanese"]
        stats["with_english"] += after["has_english"]
        row = dict(row)
        row["search_names"] = names
        row["search_japanese"] = after["japanese"]
        row["search_english"] = after["english"]
        series = (row.get("series_ids") or ["unknown"])[0]
        path = args.out / f"{series}.json"
        bucket = load(path) if path.is_file() else []
        bucket.append(row)
        path.write_text(json.dumps(bucket, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
