"""Bounded, resumable GPT Image concept queue. Draft identities never generate by accident."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from collections import Counter
from pathlib import Path
Path = _LayoutProjectPath
from types import SimpleNamespace
import argparse
import hashlib
import json; json = _LayoutJson
import re
import time
import os
from contextlib import contextmanager
import art_pipeline
from art_paths import base_concept_dir, base_concept_path

ROOT = _LayoutProjectPath(_layout_root)
CATALOG = ROOT / "content/roster/catalog.json"
STATE = ROOT / "content/roster/production.json"
JOURNAL = ROOT / "art/shared/production/attempts.jsonl"
LOCK = ROOT / "art/production/.queue.lock"


@contextmanager
def single_writer():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError("Generation queue is locked. Inspect the prior run/journal before removing a stale lock.") from None
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        LOCK.unlink()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def eligible(row):
    brief = load(ROOT / row["brief"])
    return bool(brief.get("ready_for_generation", False)) and not brief.get("required_references")


def candidate_valid(image, brief):
    metadata = image.with_suffix(".metadata.json")
    if not image.exists() or not metadata.exists():
        return False
    meta = load(metadata)
    from PIL import Image
    with Image.open(image) as source:
        alpha_valid = art_pipeline.alpha_accepted(art_pipeline.alpha_report(source))
    return alpha_valid and meta.get("image_sha256") == hashlib.sha256(image.read_bytes()).hexdigest() and meta.get("prompt_sha256") == hashlib.sha256(brief["prompt"].encode()).hexdigest()


def prior_attempt(key):
    if not JOURNAL.exists():
        return None
    matches = [json.loads(line) for line in JOURNAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    return next((record for record in reversed(matches) if record["key"] == key), None)


def journal(record):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize():
    catalog = load(CATALOG)
    reviews_path = ROOT / "art/shared/reviews/base-review.json"
    reviews = load(reviews_path)["assets"] if reviews_path.exists() else []
    state = {"schema": 1, "by_character": {}}
    for row in catalog["entries"]:
        files = sorted((ROOT / base_concept_dir(row["id"])).glob("v[0-9][0-9][0-9]/base-v*.png"))
        if not files:
            continue
        image = files[-1]
        metadata = image.with_suffix(".metadata.json")
        if not metadata.exists():
            continue
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if load(metadata).get("image_sha256") != digest:
            continue
        review = next((x for x in reviews if x["sha256"] == digest), {})
        from PIL import Image
        with Image.open(image) as source:
            alpha = art_pipeline.alpha_report(source)
        preview_path = image.relative_to(ROOT).as_posix() if art_pipeline.alpha_accepted(alpha) else ""
        state["by_character"][row["id"]] = {"path": image.relative_to(ROOT).as_posix(), "sha256": digest,
                                                   "preview_path": preview_path, "alpha": alpha,
                                                   "status": review.get("status", "awaiting_review"), "runtime_approved": False,
                                                   "notes": review.get("notes", [])}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"entries": len(catalog["entries"]), "by_kind": dict(Counter(x["kind"] for x in catalog["entries"])),
            "generation_ready": [x["id"] for x in catalog["entries"] if eligible(x)],
            "concept_characters": len(state["by_character"]), "runtime_characters": 0}


def generate(ids, revision, limit):
    with single_writer():
        return generate_locked(ids, revision, limit)


def generate_locked(ids, revision, limit):
    if not re.fullmatch(r"v\d{3}", revision) or not 1 <= limit <= 4:
        raise ValueError("Use revision v001..v999 and limit 1..4.")
    rows = {x["id"]: x for x in load(CATALOG)["entries"]}
    ids = list(dict.fromkeys(ids))
    if len(ids) > limit:
        raise ValueError("Requested IDs exceed the explicit generation limit.")
    # Validate the entire selection before the first potentially billable request.
    tasks = []
    for cid in ids:
        if cid not in rows or not eligible(rows[cid]):
            raise ValueError(f"{cid}: identity brief is still a draft; review its references before generation.")
        row = rows[cid]
        brief = load(ROOT / row["brief"])
        image = ROOT / base_concept_path(cid, revision)
        if candidate_valid(image, brief):
            print(cid + ": existing candidate and hash verified; skipped")
            continue
        if image.exists():
            raise ValueError(f"{cid}: output exists with a different brief/hash. Preserve it and use a new revision.")
        key = cid + "/" + revision
        if prior_attempt(key):
            raise ValueError(f"{key}: a prior request may have been billed. Inspect the journal and choose a new revision explicitly.")
        tasks.append((row, brief, image, key))
    for row, brief, image, key in tasks:
        journal({"key": key, "state": "request_started", "created_unix": int(time.time())})
        try:
            art_pipeline.generate_image(SimpleNamespace(model=None, reference=[], dry_run=False, out=image), brief,
                                        "roster base concept candidate; not an approved animation")
            journal({"key": key, "state": "candidate_saved", "created_unix": int(time.time())})
        except Exception:
            journal({"key": key, "state": "failed_or_uncertain_no_auto_retry", "created_unix": int(time.time())})
            raise
    return summarize()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    request = sub.add_parser("generate")
    request.add_argument("--ids", nargs="+", required=True)
    request.add_argument("--revision", default="v001")
    request.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()
    try:
        result = generate(args.ids, args.revision, args.limit) if args.command == "generate" else summarize()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
