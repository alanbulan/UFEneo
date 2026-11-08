"""列出需要重画的图鉴条目，按分片切给并行执行者。

判定“需要重画”的依据是来源缺失：条目没有 reference_source_url，说明当初
没有官方剧照可追溯，画风（玩具感）和朝向都不可信。已经有登记来源的条目
不在此列，除非显式标了 reference_is_toy。

分片用 id 的稳定哈希取模，多个执行者各拿一片，互不重叠、顺序稳定。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPLAY = ROOT / "content/roster/catalogue_display.json"
CATALOG = ROOT / "content/roster/catalog.json"
PRIORITY = {"hero": 0, "form": 1, "dark_ultra": 2, "kaiju": 3, "story": 4}


def shard_of(cid: str, total: int) -> int:
    return int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) % total


def queue() -> list[dict]:
    display = json.loads(DISPLAY.read_text(encoding="utf-8"))["entries"]
    catalog = {str(row["id"]): row for row in json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]}
    rows = []
    for cid, entry in display.items():
        toy = bool(entry.get("reference_is_toy"))
        # 重画过的条目只登记了 art_source 与 raw_sha256，没有 reference_source_url；
        # 两者都算“已有可追溯来源”，否则队列会把刚重画的条目再排一遍。
        sourced = bool(str(entry.get("reference_source_url", "")).strip()) or (
            str(entry.get("art_source", "")) == "mcp_image_to_image_from_official_reference"
            and bool(str(entry.get("raw_sha256", "")).strip())
        )
        if sourced and not toy:
            continue
        row = catalog.get(cid, {})
        rows.append({
            "id": cid,
            "title": str(row.get("title", "")),
            "name": str(row.get("name", "")),
            "form": str(row.get("form", "")),
            "kind": str(row.get("kind", "")),
            "series": (row.get("series_ids") or [""])[0],
            "reason": "toy_reference" if toy else "no_reference",
            "has_strip": bool(entry.get("strip")),
            "shard": shard_of(cid, 1),
        })
    rows.sort(key=lambda r: (r["has_strip"], PRIORITY.get(r["kind"], 9), r["series"], r["id"]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1, dest="total")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--count", action="store_true", help="只输出各分片数量")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = queue()
    if args.count:
        counts = {}
        for row in rows:
            part = shard_of(row["id"], args.total)
            counts[part] = counts.get(part, 0) + 1
        print(json.dumps({"total": len(rows), "by_shard": counts}, ensure_ascii=False))
        return 0
    mine = [r for r in rows if shard_of(r["id"], args.total) == args.shard]
    if args.limit:
        mine = mine[: args.limit]
    payload = json.dumps(mine, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
