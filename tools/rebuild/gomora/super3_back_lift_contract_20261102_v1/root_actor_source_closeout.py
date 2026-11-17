"""保全背掀十八完整源、统一整图候选与根实际看图；不安装新三级。"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
DATE = ROOT / "reports/review/2026-11-02"
ART = ROOT / "art/fighters/gomora/stage4/super3-back-lift-20261102-v1"
REGISTERED = DATE / "gomora-super3-back-lift-registration-v1/registered18-v1"
OUT = DATE / "gomora-super3-actor-sources-root-closeout-v1"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    assert not OUT.exists()
    registration = read(REGISTERED / "registration-candidate.json")
    assert len(registration["phases"]) == 18 and registration["common_scale"] == [1, 4]
    rows, total = [], Decimal("0")
    for item in registration["phases"]:
        directory = ART / f"phase-{item['phase']:02d}/request-001"
        gate = read(directory / "root-actual-source-review-v1.json")
        assert gate["actual_opened"] and gate["accepted_for_whole_action_processing"]
        assert gate["source"] == item["source"] and sha(ROOT / item["source"]["path"]) == item["source"]["sha256"]
        submission = read(directory / "submission-result.json")
        assert submission["image_returned"]
        billing = submission["official_billing"]
        total += Decimal(billing["estimated_cost_usd"])
        rows.append({"source_phase": item["phase"], "source": item["source"],
                     "root_actual_review": ref(directory / "root-actual-source-review-v1.json"),
                     "submission": ref(directory / "submission-result.json"), "native": item["native"],
                     "source_root": item["registration_root_source"]})
    views = sorted(REGISTERED.glob("*.jpg"))
    assert len(views) == 22
    fx = ROOT / "art/fighters/gomora/stage4/super3-back-lift-pixelfx-v2"
    fxviews = sorted((fx / "review-v1").glob("*-all-phases-dark-light.jpg"))
    assert len(fxviews) == 3
    OUT.mkdir()
    save(OUT / "root-source-processing-review.json", {
        "reviewer": "root_delegated_by_user", "complete_actor_sources_and_registration_accepted": True,
        "phases": rows, "registration": ref(REGISTERED / "registration-candidate.json"),
        "actual_opened_full_sequence_views": [ref(p) for p in views],
        "preview_source_order": registration["preview_source_order"],
        "order_accepted_for_next_paired_engineering_only": True,
        "actor_observation": "根实际看完整18整相深浅总页及全部17邻接页：起势双臂/肩髋下降、负重缓冲到抬髋后掀再回护可辨，双足支撑序和完整长尾保持。07→09→08→10→11只作新预览序，原请求相号/raw tick不回改。11→12快速下沉与脚距/爪底小差保留，尚未看配对实机。",
        "pixelfx_candidate": ref(fx / "delivery-final-manifest.json"),
        "actual_opened_pixelfx_views": [ref(p) for p in fxviews],
        "pixelfx_observation": "v1过稀未收最终；v2离线完整帧的释放拖尘与低位两翼落地尘已有体积和渐散，允许候选接线，实际世界挂点/遮挡/触发仍待配对实机。",
        "victim_inventory": ref(DATE / "gomora-super3-victim-s5-whole-inventory-v1/actual-visual-review.json"),
        "victim_review_attribution": "九对象S5实看归执行席；根核其报告，未冒称根亲开全部九人反应页。",
        "victim_whole_transition_missing": True, "paired_grip_and_capture_geometry_accepted": False,
        "full_move_main_runtime_accepted": False, "new_special3_installed": False,
        "old_special3_kept": ref(ROOT / "content/fighters/gomora/moves/special3.json"),
        "strict_size_passed": False, "per_phase_area_fit": False, "body_parts_composited": False,
        "alpha_quarantine_preserved": True, "serial_order_deviation_preserved": True,
        "actor_18_sources_estimated_cost_usd": str(total),
        "latest_project_committed_usd": "49.985414", "project_limit_usd": "60.00",
        "unknown_old_request_reservation_included_usd": "10.00", "account_balance_queried": False,
        "goal_status": "active"})
    (OUT / "README.md").write_text(
        "# 哥莫拉三级背掀：十八完整本人源与PixelFX候选\n\n"
        "十八张独立完整本人源已逐张根实看接受，并以同一1/4整图倍率、512×320画布和根[256,304]注册。根又看完全部深浅总页与17邻接页，允许按07→09→08→10→11的新预览序进入下一步配对；原源相号、请求raw tick、弱Alpha隔离及先前串行看图顺序偏差记录均保持。不做逐相面积拟合或拼肢，严格尺寸、快速下沉和爪底小差不冒称修完。\n\n"
        "PixelFX首版尘点过稀，已保全；第二版独立重新烘焙为释放拖尘和低位两侧体积土尘，根实际看三套完整深浅页后允许候选接线。固定MIT版本、参数、根点、Alpha与重复烘焙证据齐，尚未核实际遮挡/世界挂点。\n\n"
        "执行席实查杰顿、赛文、四英雄、两EX及哥莫拉的S5完整反应格：两EX虽有贴地俯伏源，九对象都缺接背、横伏负重、抬升到脱手的连续整相。不能旋转仰卧或只加waist点替代。因此新三级未安装，旧三级波保持运行；捕获框和双方承接须在真受方整相齐后继续。\n\n"
        "本机累计占额49.985414/60美元，含旧未知10美元；这不是接口账户余额。Goal继续active。\n",
        encoding="utf-8", newline="\n")
    folders = [ART, ROOT / "art/fighters/gomora/stage4/super3-back-lift-pixelfx-v1", fx,
               DATE / "gomora-back-lift-new-sources-v1", DATE / "gomora-super2-newsource-v1",
               ROOT / "tools/rebuild/gomora/super3_back_lift_contract_20261102_v1",
               ROOT / "tools/rebuild/gomora/super3_back_lift_pixelfx_20261102_v1",
               ROOT / "tools/rebuild/gomora/super3_back_lift_pixelfx_20261102_v2"]
    folders += [p for p in DATE.iterdir() if p.is_dir() and p.name.startswith("gomora-super3-")]
    files = {p for folder in folders for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    files.update([ROOT / ".gitattributes", ROOT / "docs/HANDBOOK.md",
                  ROOT / "tools/rebuild/shared/root_whole_source_review_20261102.py"])
    names = sorted(p.relative_to(ROOT).as_posix() for p in files)
    save(OUT / "precise-paths.json", {"files": names, "source_reference_video_kept": True,
                                      "generated_movie_included": False})
    names.append((OUT / "precise-paths.json").relative_to(ROOT).as_posix())
    (OUT / "commit-paths.nul").write_bytes(b"\0".join(x.encode() for x in sorted(set(names))) + b"\0")
    print(json.dumps({"report": str(OUT), "actor_processing_accepted": True, "special3_installed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
