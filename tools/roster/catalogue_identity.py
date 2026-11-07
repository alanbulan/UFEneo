"""图鉴生产前的只读身份/资源查询；唯一运行别名来源为 catalogue_display.aliases。"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from roster.chinese_text import simplified_text

ROOT = Path(__file__).resolve().parents[1]
GENERIC = {"奥特曼", "怪兽", "宇宙人", "星人", "ultraman", "monster", "alien",
           "火型态", "火形态", "水型态", "水形态"}
PREFIX = re.compile(r"^(?:(?:古代|透明|地底|甲虫|犬狼|触手|海贼|宇宙|杀手|强化|虚拟|合体|最强|超古代|污染|冷冻|岩石|暴君|变身|凶恶|宇宙甲壳))*(?:怪兽|宇宙人|超兽|龙兽|生命体)")
# 只有整串是普通称号＋单一本名时才提取片假名。命名形态、代数、
# 具名个体、型号和“宇宙赛文加”这类限定词必须留在身份里。
JAPANESE_SIMPLE_NAME = re.compile(
    r"(?:(?:(?:冷凍|透明|地底|古代|宇宙|凶悪|合体|超古代)(?:怪獣|宇宙人)|宇宙忍者)\s*)?"
    r"(?P<name>[\u30a0-\u30ffー]{3,})(?:星人|怪獣|超獣)?"
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


def identity_tokens(row):
    """保留完整命名形态；跨语言别名只用于找待核命中，不自行判等。"""
    tokens = set()
    for value in [row.get("name", ""), row.get("display_name", ""), *row.get("aliases", [])]:
        if not isinstance(value, str):
            continue
        display = simplified_text(value)
        candidates = [value, display, PREFIX.sub("", value.strip()), PREFIX.sub("", display.strip())]
        simple = JAPANESE_SIMPLE_NAME.fullmatch(unicodedata.normalize("NFKC", value).strip())
        if simple:
            candidates.append(simple.group("name"))
        for candidate in candidates:
            token = normalized(candidate)
            if len(token) >= 3 and normalized(simplified_text(candidate)) not in GENERIC:
                tokens.add(token)
    return tokens


def source_token(value):
    """本人百科/官方角色或商品页可跨译名找重；作品维基页面不作本人键。"""
    if not isinstance(value, str):
        return None
    url = urlsplit(value)
    # 官方商店一个商品页可以包含整套不同人物/形态，页URL不是单一本人键。
    # 来源仍完整保存；本人名字和独立参考图SHA继续参与排重。
    if url.netloc.casefold() == "store.m-78.jp":
        return None
    trusted = ((url.netloc.endswith("tsuburaya-prod.com") and url.path.startswith("/encyclopedia/"))
               or (url.netloc.endswith("m-78.jp") and url.path.startswith(("/character/", "/products/")))
               or (url.netloc.endswith("tamashiiweb.com") and url.path.startswith("/item/")))
    return "url:" + url.netloc.casefold() + url.path.rstrip("/") if trusted else None


def resolve_alias(identity, aliases):
    chain = [identity]
    while identity in aliases:
        target = aliases[identity]
        if not isinstance(target, str) or not target or target in chain:
            raise ValueError("图鉴别名链为空、无效或成环: " + " -> ".join(chain))
        identity = target
        chain.append(identity)
    return identity, chain


def alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return bool(ok) and code.value == 259
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class IdentityIndex:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.catalog = {r["id"]: r for r in read(self.root / "content/roster/catalog.json")["entries"]}
        display = read(self.root / "content/roster/catalogue_display.json")
        self.entries, self.aliases = display["entries"], display.get("aliases", {})
        for row in display.get("supplemental_entries", []):
            self.catalog.setdefault(row["id"], row)
        self.planned = {}
        planned_path = self.root / "art/shared/catalogue-fill/planned-identities.json"
        if planned_path.is_file():
            planned = read(planned_path)
            if planned.get("schema") != "ufeneo.planned-catalogue-identities.v1":
                raise ValueError("离线图鉴身份计划版本无效")
            for row in planned["entries"]:
                identity = row["id"]
                if identity in self.catalog or row.get("generation_approved") is not True:
                    continue
                if not row.get("sources") or not row.get("evidence_files"):
                    raise ValueError("离线身份缺少本人来源: " + identity)
                self.catalog[identity] = row
                self.planned[identity] = row
        self.resources = {}
        for identity, entry in self.entries.items():
            image = self.path(entry.get("image", ""))
            if image and image.is_file():
                self.resources.setdefault(identity, {})["catalogue_image"] = self.rel(image)
        for path in (self.root / "content/fighters").glob("*/definition.json"):
            identity = path.parent.name
            manifest = self.root / "assets/fighters" / identity / "animations/manifest.json"
            model = self.root / "assets/fighters" / identity / "model-native.png"
            if manifest.is_file() or model.is_file():
                row = self.resources.setdefault(identity, {})
                row["battle_definition"] = self.rel(path)
                for label, resource in (("battle_manifest", manifest), ("battle_model", model)):
                    if resource.is_file():
                        row[label] = self.rel(resource)
                definition = read(path)
                if identity not in self.catalog:
                    self.catalog[identity] = dict(id=identity, name=definition.get("display_name", identity))
        self.tokens = {identity: identity_tokens(row) for identity, row in self.catalog.items()}
        for identity, row in self.catalog.items():
            token = source_token(row.get("official_url"))
            if token:
                self.tokens[identity].add(token)
            for source in self.planned.get(identity, {}).get("sources", []):
                token = source_token(source.get("page_url"))
                if token:
                    self.tokens[identity].add(token)
                self.tokens[identity].add("identity-reference-sha256:" + source["sha256"])
        for identity, entry in self.entries.items():
            profile_path = self.path(entry.get("profile", ""))
            if profile_path and profile_path.is_file():
                token = source_token(read(profile_path).get("source_url"))
                if token:
                    self.tokens.setdefault(identity, set()).add(token)
        pool = self.root / "art/shared/catalogue-fill/source213-new-identities/source-inventory.json"
        if pool.is_file():
            for row in read(pool)["entries"]:
                tokens = self.tokens.setdefault(row["id"], set())
                for source in row.get("sources", []):
                    token = source_token(source.get("page_url"))
                    if token:
                        tokens.add(token)
                    if source.get("sha256"):
                        tokens.add("identity-reference-sha256:" + source["sha256"])

    def rel(self, path):
        return path.relative_to(self.root).as_posix()

    def path(self, value):
        return self.root / value.removeprefix("res://") if value else None

    def source_state(self, identity, ignore_inflight_out=None):
        """只查当前身份目录/账本，不再遍历耗尽的全项目旧 raw 池。"""
        folder = self.root / "art/fighters" / identity / "stage1/catalogue/generation"
        returned = []
        if folder.is_dir():
            for pattern in ("**/raw.png", "**/raw.provider.png"):
                returned.extend(self.rel(p) for p in folder.glob(pattern) if p.is_file())
        inflight = []
        work = self.root / "art/shared/catalogue-fill"
        for pattern in (f"*/{identity}/ledger.json", f"*/*/{identity}/ledger.json"):
            for path in work.glob(pattern):
                job_path = path.with_name("job.json")
                job = read(job_path) if job_path.is_file() else {}
                if ignore_inflight_out and self.path(job.get("out", "")) == Path(ignore_inflight_out):
                    continue
                for request in read(path).get("requests", []):
                    if request.get("status") == "inflight" and alive(request.get("pid")):
                        inflight.append(dict(ledger=self.rel(path), pid=request["pid"], out=job.get("out")))
        return dict(returned=sorted(set(returned)), inflight=inflight)

    def query(self, identity, *, reserved=(), ignore_inflight_out=None):
        result = dict(id=identity, decision="needs_identity_review", canonical_id=identity,
                      alias_source="content/roster/catalogue_display.json.aliases", hits=[])
        try:
            canonical, chain = resolve_alias(identity, self.aliases)
        except ValueError as exc:
            return dict(result, reason=str(exc))
        result.update(canonical_id=canonical, alias_chain=chain)
        if identity in self.planned:
            for evidence in self.planned[identity]["evidence_files"]:
                path = (self.root / evidence["path"]).resolve()
                if not path.is_relative_to(self.root.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != evidence["sha256"]:
                    raise ValueError("离线身份来源文件缺失或SHA不符: " + identity)
            result.update(planned_identity=self.planned[identity], runtime_registration=False)
        if identity not in self.catalog and canonical not in self.catalog:
            return dict(result, reason="未登记身份，先核本体、命名形态与明确版本。")
        exact = self.resources.get(canonical) or self.resources.get(identity)
        if exact:
            return dict(result, decision="reuse", reason="已有正式人物/图鉴资源，复用本人资源。", resources=exact)
        state = self.source_state(canonical, ignore_inflight_out)
        if canonical != identity:
            alias_state = self.source_state(identity, ignore_inflight_out)
            state = dict(returned=sorted(set(state["returned"] + alias_state["returned"])),
                         inflight=state["inflight"] + alias_state["inflight"])
        result["source_state"] = state
        tokens = self.tokens.get(identity, self.tokens.get(canonical, set()))
        candidates = set(self.catalog) | set(reserved)
        for other in sorted(candidates - {identity, canonical}):
            overlap = sorted(tokens & self.tokens.get(other, set()))
            if not overlap:
                continue
            other_canonical, _ = resolve_alias(other, self.aliases)
            resources = self.resources.get(other_canonical) or self.resources.get(other)
            other_state = self.source_state(other) if not resources else {}
            if resources or other_state.get("returned") or other_state.get("inflight") or other in reserved:
                result["hits"].append(dict(id=other, canonical_id=other_canonical,
                    name=self.catalog.get(other, {}).get("name"), matching_identity_tokens=overlap,
                    series_ids=self.catalog.get(other, {}).get("series_ids", []),
                    resources=resources, source_state=other_state, reserved_in_current_batch=other in reserved))
        if result["hits"]:
            return dict(result, reason="跨语言别名/本人命中；先核命名形态/版本，不能仅按不同ID、集数、姿势或作品重生。")
        if state["returned"] or state["inflight"]:
            return dict(result, decision="reuse", reason="本人已有返回源或活请求，不再生成首图。")
        return dict(result, decision="generate", reason="无canonical、正式人物、同本人图鉴、已返回源或活请求命中。")


class CatalogueIdentityError(ValueError):
    """身份门拒绝；调用方应单列跳过，不能当接口故障每五分钟重试。"""


def require_runtime_repair(index, identity, result, basis):
    """允许已实审玩具硬错在原canonical下出新候选，不给重复首图豁免。"""
    def reject():
        raise CatalogueIdentityError('已装图鉴返修缺少同本人当前运行SHA或真实审阅证据。')

    if not isinstance(basis, dict) or basis.get('schema') != 'ufeneo.catalogue-runtime-repair.v1':
        reject()
    if result.get('canonical_id') != identity or basis.get('canonical_id') != identity:
        reject()
    image = result.get('resources', {}).get('catalogue_image')
    if not image or index.path(basis.get('runtime_image', '')) != index.path(image):
        reject()
    root = index.root.resolve()
    def checked_file(path_value, expected, *, review=False):
        path = index.path(path_value)
        if not path:
            reject()
        path = path.resolve()
        if not path.is_relative_to(root) or not path.is_file():
            reject()
        if review and not path.is_relative_to(root / 'reports/review'):
            reject()
        if not isinstance(expected, str) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            reject()
        return path

    checked_file(image, basis.get('runtime_image_sha256'))
    allowed = {'toy_joint_seam', 'toy_ball_joint', 'toy_pivot_hole', 'toy_molding_gap'}
    defects = basis.get('defects')
    if (not isinstance(defects, list) or not defects or not all(isinstance(d, str) for d in defects)
            or not set(defects).issubset(allowed)):
        reject()
    record_path = checked_file(basis.get('review_record', ''), basis.get('review_record_sha256'), review=True)
    review = read(record_path)
    if not isinstance(review, dict) or review.get('actual_view') is not True:
        reject()
    rows = [r for r in review.get('entries', []) if isinstance(r, dict) and r.get('id') == identity]
    if len(rows) != 1:
        reject()
    row = rows[0]
    if (index.path(row.get('runtime_image', '')) != index.path(image)
            or row.get('runtime_image_sha256') != basis.get('runtime_image_sha256')
            or set(row.get('defects', [])) != set(defects)):
        reject()
    pages = row.get('actual_opened_pages')
    if not isinstance(pages, list) or not pages:
        reject()
    for page in pages:
        if not isinstance(page, dict) or page.get('actual_opened') is not True:
            reject()
        checked_file(page.get('path', ''), page.get('sha256'))
    return dict(result, decision='repair_existing_runtime', runtime_repair_basis=basis,
        runtime_preserved_until_approved_replacement=True, new_identity=False)


def require_catalogue_generation(args, brief):
    """在网络/密钥读取前拦图鉴重复首图；不影响战斗动作/特效生产。"""
    out = Path(args.out).resolve()
    try:
        parts = out.relative_to(ROOT / "art/fighters").parts
    except ValueError:
        return None
    if len(parts) < 5 or parts[1:4] != ("stage1", "catalogue", "generation"):
        return None
    identity = brief.get("character_id") or parts[0]
    if identity != parts[0]:
        raise CatalogueIdentityError("图鉴请求身份与输出目录不一致。")
    index = IdentityIndex()
    result = index.query(identity, ignore_inflight_out=out.parent)
    if brief.get('runtime_repair_basis') is not None:
        return require_runtime_repair(index, identity, result, brief['runtime_repair_basis'])
    if result["decision"] == "generate":
        return result
    # 尚未入运行的坏候选可以在原身份下明确返修，不能借返修生成已有正式本人资源。
    repair = brief.get("repair_basis") or brief.get("repair_method")
    if repair and result.get("canonical_id") == identity and result.get("source_state", {}).get("returned") and not result.get("resources") and not result.get("hits"):
        return dict(result, decision="repair_existing_candidate")
    raise CatalogueIdentityError("图鉴生产前身份门: " + json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identities", nargs="+")
    args = parser.parse_args()
    index = IdentityIndex()
    print(json.dumps(dict(entries=[index.query(identity) for identity in args.identities]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
