"""从已保存的评测页 HTML 提取图片 URL 并下载大图（只用于本轮侧视筛选）。"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
DIR = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/candidates-side"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


def main() -> int:
    source = DIR / "inkdgeek.html"
    text = source.read_text(encoding="utf-8", errors="ignore")
    urls = re.findall(r"https://blogger\.googleusercontent\.com/[^\"' ]+", html.unescape(text))
    unique = []
    for url in urls:
        base = url.split("=")[0]
        if base in {u.split("=")[0] for u in unique}:
            continue
        unique.append(url)
    rows = []
    for index, url in enumerate(unique, start=1):
        # 博客缩略图为 s640，换 s1600 取大图。
        big = re.sub(r"/s\d+/", "/s1600/", url)
        name = f"inkdgeek-{index:02d}.jpg"
        target = DIR / name
        try:
            request = urllib.request.Request(
                big, headers={"User-Agent": UA, "Referer": "https://inkdgeek.blogspot.com/"})
            body = urllib.request.urlopen(request, timeout=90).read()
            target.write_bytes(body)
            rows.append({"file": name, "url": big, "bytes": len(body),
                         "sha256": hashlib.sha256(body).hexdigest()})
            print("saved", name, len(body))
        except Exception as error:
            print("ERR", name, error)
    (DIR / "downloads.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
