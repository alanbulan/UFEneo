"""Import revision-linked Wikipedia research, never fabricated frame or move data."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from datetime import datetime, timezone
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import hashlib
import json; json = _LayoutJson
import re
import urllib.parse
import urllib.request
import urllib.error
import time
import mwparserfromhell
from roster.chinese_text import simplified_text, select_chinese_variant

ROOT = _LayoutProjectPath(_layout_root)
DEST = ROOT / "docs/research/wikipedia"
PAGES = {
    "ultraman": "初代奥特曼", "seven": "赛文奥特曼", "jack": "归来的奥特曼", "ace": "艾斯奥特曼",
    "taro": "泰罗奥特曼", "leo": "超人力霸王雷歐", "joneus": "The Ultraman", "80": "超人力霸王80",
    "usa": "超人力霸王USA", "great": "葛雷奥特曼", "powered": "超人力霸王帕瓦德", "zearth": "超人力霸王傑斯",
    "tiga": "迪迦奥特曼", "dyna": "戴拿奥特曼", "gaia": "盖亚奥特曼", "nice": "超人力霸王耐斯",
    "neos": "超人力霸王涅歐斯", "cosmos": "高斯奥特曼", "nexus": "奈克瑟斯奥特曼", "max": "超人力霸王馬克斯",
    "mebius": "梦比优斯奥特曼", "zero": "赛罗·奥特曼_THE_MOVIE_超决战！贝利亚银河帝国", "saga": "奥特曼传奇", "ginga": "银河奥特曼",
    "x": "艾克斯奥特曼", "orb": "欧布奥特曼", "geed": "捷德奥特曼", "rb": "超人力霸王R / B",
    "taiga": "泰迦奥特曼", "galaxy_fight": "奥特银河格斗", "z": "泽塔奥特曼", "trigger": "特利迦奥特曼",
    "shin": "新·奥特曼", "decker": "德凯奥特曼", "regulos": "超人力霸王雷古洛斯", "blazar": "布莱泽奥特曼",
    "rising": "ULTRAMAN：崛起", "arc": "亚刻奥特曼", "omega": "超人力霸王OMEGA", "teo": "超人力霸王狄奧",
    "seven_x": "超人七號X",
}
CHARACTERS = {
    "ultraman": "Ultraman (character)", "ultraseven": "Ultraseven (character)",
    "ultraman-tiga": "Ultraman Tiga (character)", "ultraman-zero": "Ultraman Zero",
    "ultraman_belial": "Ultraman Belial", "ultraman-orb": "List of Ultraman Orb characters",
    "ultraman-geed": "List of Ultraman Geed characters",
}
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
PARSER_VERSION = 3


def plain(text):
    code = mwparserfromhell.parse(select_chinese_variant(text))
    for template in reversed(code.filter_templates(recursive=True)):
        name = str(template.name).strip().lower()
        param = 2 if name in {"lang", "langx"} else 1
        if (re.fullmatch(r"nihongo\d*", name) or name in {"jpn", "lang", "langx", "le", "tsl"}) and template.has(param):
            try:
                code.replace(template, str(template.get(param).value), recursive=True)
            except ValueError:
                pass
    # Identity extraction also uses plain(); display localization must not change
    # its matching keys or collapse film-world versions into the original hero.
    return simplified_text(re.sub(r"\n{3,}", "\n\n", code.strip_code(normalize=True, collapse=True)).strip(), canonical_names=False)


def categories(heading):
    rules = {
        "skills": r"必殺|必杀|技能|能力|武器|裝備|装备|光線|光线|powers|abilities",
        "forms": r"型態|形態|形态|型态|フォーム|other forms",
        "story": r"故事|劇情|剧情|經歷|经历|history|plot|synopsis|story",
        "characters": r"角色|登場|登场|怪獸|怪兽|宇宙人|主角|character|human hosts",
    }
    return [tag for tag, pattern in rules.items() if re.search(pattern, heading, re.I)]


def sections(wikitext):
    pieces = re.split(r"(?m)^(={2,6})\s*(.*?)\s*\1\s*$", wikitext)
    result = []
    stack = []
    for index in range(1, len(pieces), 3):
        level, heading, body = len(pieces[index]), simplified_text(plain(pieces[index + 1])), pieces[index + 2]
        while stack and stack[-1][0] >= level:
            stack.pop()
        own = categories(heading)
        inherited = list(dict.fromkeys([tag for _, tags in stack for tag in tags]))
        tags = list(dict.fromkeys(own + inherited))
        stack.append((level, own))
        text = simplified_text(plain(body))
        if tags and text:
            terms = []
            for term in re.findall(r"'''([^'\n]{2,90})'''", body) + re.findall(r"(?m)^\*\s*([^\n]{2,100})", body):
                term = simplified_text(re.split(r"[（(]", plain(term))[0].strip("* :；;"))
                if 2 <= len(term) <= 60 and not re.search(r"速度|身高|體重|体重|噸|吨|公尺|马赫|馬赫|[:：∶]", term):
                    terms.append(term)
            result.append({"heading": heading, "level": level, "categories": tags, "text": text,
                           "candidate_terms": list(dict.fromkeys(terms))})
    return result


def api(lang, **params):
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"format": "json", **params})
    request = urllib.request.Request(url, headers={"User-Agent": "UFEneoResearch/1.0 (local game research; revision attribution retained)"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 0:
                delay = min(45, max(5, int(exc.headers.get("Retry-After", "20"))))
                print(f"Wikipedia rate limit; honoring Retry-After {delay}s before one read-only retry.", flush=True)
                time.sleep(delay)
            else:
                raise


def batch(jobs):
    """MediaWiki supports up to 50 titles; batch instead of rapid per-page requests."""
    parsed = {}
    for lang in sorted(set(job[2] for job in jobs)):
        selected = [job for job in jobs if job[2] == lang]
        for offset in range(0, len(selected), 40):
            group = selected[offset:offset + 40]
            result = api(lang, action="query", titles="|".join(job[1] for job in group), redirects=1,
                         prop="revisions", rvprop="ids|content", rvslots="main")
            query = result.get("query", {})
            renames = {x["from"]: x["to"] for x in query.get("normalized", []) + query.get("redirects", [])}
            pages = {x["title"]: x for x in query.get("pages", {}).values()}
            for key, title, _, _ in group:
                visited = set()
                while title in renames and title not in visited:
                    visited.add(title)
                    title = renames[title]
                page = pages.get(title, {})
                if "revisions" in page:
                    rev = page["revisions"][0]
                    parsed[key] = {"parse": {"title": page["title"], "pageid": page["pageid"], "revid": rev["revid"],
                                              "wikitext": {"*": rev["slots"]["main"]["*"]}}}
                else:
                    parsed[key] = {"error": {"code": "missingtitle"}}
            time.sleep(2)
    return parsed


def fetch(job, supplied=None):
    key, requested, lang, target = job
    file = DEST / (key + ".json")
    if file.exists():
        old = json.loads(file.read_text(encoding="utf-8"))
        if old.get("status") == "fetched" and old.get("requested_title") == requested:
            cache = ROOT / ".references/wikipedia" / (key + ".wiki")
            if old.get("parser_version") != PARSER_VERSION and cache.exists():
                old.update(sections=sections(cache.read_text(encoding="utf-8")), parser_version=PARSER_VERSION)
                persist(old)
            return old
    result = {"id": key, "target": target, "requested_title": requested, "language": lang, "status": "missing",
              "license": LICENSE, "sections": [], "parser_version": PARSER_VERSION}
    try:
        data = supplied if supplied is not None else api(lang, action="parse", page=requested, prop="sections|wikitext", redirects=1)
        if "parse" not in data:
            result["error"] = data.get("error", {}).get("code", "unknown")
        else:
            page = data["parse"]
            raw = page["wikitext"]["*"]
            url = f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(page["title"].replace(" ", "_"))
            rev = page.get("revid")
            result.update(status="fetched", title=page["title"], page_id=page["pageid"], revision_id=rev,
                          url=url, revision_url=f"https://{lang}.wikipedia.org/w/index.php?oldid={rev}",
                          authors_url=f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(page['title'])}&action=history",
                          retrieved_utc=datetime.now(timezone.utc).isoformat(),
                          wikitext_sha256=hashlib.sha256(raw.encode()).hexdigest(), sections=sections(raw))
            cache = ROOT / ".references/wikipedia"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / (key + ".wiki")).write_text(raw, encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        result.update(status="fetch_failed", error=type(exc).__name__)
    persist(result)
    return result


def persist(result):
    DEST.mkdir(parents=True, exist_ok=True)
    if result.get("language") == "zh":
        result["display_title"] = simplified_text(result.get("title", result["requested_title"]))
        result["display_language"] = "zh-CN"
        result["text_changes"] = "抽取、去除维基标记、选择简体变体、OpenCC简体转换与已核定大陆角色译名统一；原始缓存和固定修订不变"
    (DEST / (result["id"] + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result["status"] == "fetched":
        lines = ["# " + result.get("display_title", result["title"]) + " · 维基百科研究摘录", "",
                 f"来源：[页面]({result['url']}) · [固定修订]({result['revision_url']}) · [作者历史]({result['authors_url']})", "",
                 f"本文由维基百科文本抽取、去除标记并按章节整理；中文正文统一为简体中文与已核定大陆角色译名，来源原页标题保留在元数据中。原文及本摘录适用 [CC BY-SA 4.0]({LICENSE})；引用资料与图片可能采用不同许可。", "",
                 "以下是研究资料，尚未转换为已验收的角色技能或原作帧数据。", ""]
        for section in result["sections"]:
            lines.extend(["## " + section["heading"], "", section["text"], ""])
        (DEST / (result["id"] + ".md")).write_text("\n".join(lines), encoding="utf-8")


def rebuild_indexes():
    # Rebuild the complete local index even for a targeted incremental run.
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DEST.glob("*.json")) if p.name not in {"index.json", "term-index.json"}]
    index = [{k: record[k] for k in ["id", "target", "status", "language", "requested_title"]} |
             {k: record[k] for k in ["title", "display_title", "display_language", "url", "revision_url", "revision_id", "license"] if k in record} |
             {"targets": record["target"].split(","), "file": f"docs/research/wikipedia/{record['id']}.json", "markdown": f"docs/research/wikipedia/{record['id']}.md",
              "section_counts": {tag: sum(tag in s["categories"] for s in record["sections"]) for tag in ["skills", "forms", "story", "characters"]}}
             for record in records]
    (DEST / "index.json").write_text(json.dumps({"schema": 1, "pages": index}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    terms = []
    for record in records:
        for section in record["sections"]:
            if "forms" not in section["categories"] and "skills" not in section["categories"]:
                continue
            for term in section.get("candidate_terms", []):
                terms.append({"term": term, "categories": section["categories"], "targets": record["target"].split(","),
                              "source": record["id"], "heading": section["heading"], "revision_url": record["revision_url"],
                              "status": "extracted_candidate_requires_subject_and_name_review"})
    (DEST / "term-index.json").write_text(json.dumps({"schema": 1, "license": LICENSE, "terms": terms}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh_offline():
    count = 0
    for path in sorted(DEST.glob("*.json")):
        if path.name in {"index.json", "term-index.json"}:
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("status") != "fetched" or row.get("language") != "zh":
            continue
        raw = (ROOT / ".references/wikipedia" / (row["id"] + ".wiki")).read_text(encoding="utf-8")
        if hashlib.sha256(raw.encode()).hexdigest() != row["wikitext_sha256"]:
            raise ValueError("Source cache differs from recorded revision: " + row["id"])
        row.update(sections=sections(raw), parser_version=PARSER_VERSION)
        persist(row)
        count += 1
    rebuild_indexes()
    print("Simplified Chinese documents rebuilt from unchanged cached revisions:", count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--offline", action="store_true", help="Normalize existing Chinese research without network requests")
    parser.add_argument("--follow-main", action="store_true", help="Also ingest linked character-list main articles")
    args = parser.parse_args()
    if args.offline:
        refresh_offline()
        return
    jobs = [("series_" + k, v, "zh", k) for k, v in PAGES.items()]
    jobs += [("character_" + k, v, "en", k) for k, v in CHARACTERS.items()]
    jobs += [("master_heroes", "超人力霸王列表", "zh", ",".join(PAGES)),
             ("list_max_kaiju", "超人力霸王馬克斯怪獸列表", "zh", "max"),
             ("character_zh_ultraman", "初代超人力霸王", "zh", "ultraman"),
             ("character_zh_zoffy", "佐菲", "zh", "ultraman,galaxy_fight"),
             ("character_zh_gomora", "哥摩拉", "zh", "ultraman"),
             ("character_zh_zetton", "傑頓", "zh", "ultraman")]
    if args.ids:
        jobs = [job for job in jobs if job[3] in args.ids]
    if args.follow_main:
        links = {}
        for path in (ROOT / ".references/wikipedia").glob("series_*.wiki"):
            target = path.stem.removeprefix("series_")
            if args.ids and target not in args.ids:
                continue
            code = mwparserfromhell.parse(path.read_text(encoding="utf-8"))
            for template in code.filter_templates():
                if str(template.name).strip().lower() not in {"main", "主條目", "主条目"}:
                    continue
                for param in template.params:
                    title = str(param.value).split("#")[0].strip()
                    if re.search("角色|登場人物|怪獸|怪兽", title):
                        links.setdefault(title, set()).add(target)
        for title, targets in links.items():
            key = "related_" + hashlib.sha256(title.encode()).hexdigest()[:12]
            jobs.append((key, title, "zh", ",".join(sorted(targets))))
    needed = []
    for job in jobs:
        path = DEST / (job[0] + ".json")
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if old.get("status") != "fetched" or old.get("requested_title") != job[1]:
            needed.append(job)
    supplied = batch(needed) if needed else {}
    results = [fetch(job, supplied.get(job[0])) for job in jobs]
    rebuild_indexes()
    for result in results:
        print(result["id"], result["status"], result.get("title", result.get("error")), len(result["sections"]))


if __name__ == "__main__":
    main()
