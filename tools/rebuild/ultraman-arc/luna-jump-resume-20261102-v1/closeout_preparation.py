"""保全本席真实看图记录与精确归属；不碰产品、共享文档或Git。"""
from pathlib import Path
import ast
import hashlib
import json
import sys

sys.dont_write_bytecode = True
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "reports/review/2026-11-02/luna-jump-resume-guides-v2"
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v2"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text("utf-8-sig"))
def rel(path):return path.resolve().relative_to(ROOT).as_posix()
def ref(path):return {"path": rel(path), "sha256": sha(path)}
def save(path, data):
    assert not path.exists()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    contract = read(ART / "jump-resume-contract.json")
    views = [ROOT / row["JPEG_preview"]["path"] for row in contract["new_air_guide_briefs_for_root_review"]]
    old = ROOT / "reports/review/2026-11-02/arc-luna-jump-ground-four-guides-v2"
    views.extend(old / name for name in ["same-complete-identity-master.jpg", "takeoff-00-complete-guide.jpg", "takeoff-01-complete-guide.jpg", "land-00-complete-guide.jpg", "land-01-complete-guide.jpg"])
    for path in views:
        with Image.open(path) as picture:
            assert picture.format == "JPEG" and picture.width <= 768 and path.stat().st_size <= 150000
    for path in HERE.glob("*.py"):ast.parse(path.read_text("utf-8"), filename=rel(path))
    receipt = read(OUT / "preflight-receipt.json")
    assert all(sha(ROOT / row["path"]) == row["sha256"] for row in receipt["protected_original_bytes"])
    save(OUT / "subagent-actual-visual-review.json", {"reviewer": "/root/luna_jump_resume", "actually_opened_complete_JPEGs": [ref(path) for path in views], "observations": ["既有起落四张保持近亮后左/远暗前右脚序，双臂肩胸髋一同压膝/蹬伸与吸震/回护；root旧预审仍是抽象姿态范围。", "垂直五张由收腿、深收束、短平衡到伸腿接地，近远整肢可追踪，两整臂均在变化。", "前翻头右下→头左下、后翻横身→倒立方向可读；v2眼部箭头随完整头部耳眼轴旋转。v1固定右箭头明确拒用并保全。", "共同规划长度/159比例只属master表面代理，不是返回人物或严尺。末相仍须真实人物审尺寸、双靴、肩腕圆盘/装甲和Alpha。"], "scope_accepted_by_subagent": "可交根预审的完整抽象姿态；不批准收费、人物、严尺或运行", "root_actual_new_air_guide_review": False, "person_sources_accepted": False, "main_or_replay_accepted": False})
    save(OUT / "runtime-tool-readiness.json", {"entry": ref(HERE / "main_entry.gd"), "factory": ref(HERE / "candidate_factory.gd"), "driver": ref(HERE / "main_driver.gd"), "main_adapter": ref(HERE / "main_game.gd"), "python_runner": ref(HERE / "runtime_bundle.py"), "python_AST_and_cli_help_valid": True, "GDScript_parsed_by_engine": False, "Godot_started": False, "freeze_executed": False, "runtime_candidate_created": False, "requires": "17张真实月亮本人整源、共同159整图/320/根160,280注册包与根完整画面批准；缺任一则freeze前拒绝。", "actual_main_expected_scope": "720/1080双向自然8/9/7 InputFrame；n0/1起跳、n2..32空中31tick、n16/17高136双顶点、n33..36落地、n37idle；逐tick对模拟相/表现相/位移高度；完整Alpha屏内和原输入独立可见回放。", "not_human_keyboard": True, "no_product_or_formal_flags_changed": True})
    (OUT / "README.md").write_text("""# 月亮基础跳跃接续准备

四张既有起跳/落地brief及全部附件SHA已复核，项目客户端四次纯dry-run均产生high、1024方图、transparent及两个实际参考；没有网络POST或输出人物。原四guide已有根实际预审，本席又打开同一master和四张完整JPEG，不重做走、冲刺、后撤、蹲或闪避。

可先交根提交的首张仍是 `art/fighters/ultraman-arc__luna/stage2/jump-ground-guides-20261102-v2/takeoff/phase-00/brief.json`，SHA `fba4afa469afe2ae84c6b7d1aba5f4e6e7e3eb839e8771f0bf1e40d3506415a3`。参考顺序为抽象guide `dfbaa22b071ad1acd658527584356d6d0c2e0644c1625de8842695cde7c56a1d`、同一本人master `d70d0f5fba22d54281b50703158ac2ba8ff1d29624f3020b4bdbe7c20992a6da`。根按最新1美元预占/60上限/旧未知10占额串行处理；历史旧预审中的10美元政策不改字节，本工具未读写预算或密钥。

新增垂直5/前翻4/后翻4份完整整人合同、独立抽象guide、prompt和表面代理目标，见 `art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v2/jump-resume-contract.json`。本席已实际打开全部十三张完整合规JPEG。两整臂、肩胸髋和双腿共同变化，同一近亮/远暗身份保持，前后翻各自新画。没有采样、旋转或拼接人物像素。共同master表面代理等长不当真人骨尺；共同159比例尚须返回人物实测。

首版新增空中guide实际审图发现眼部箭头固定朝右，会与倒立/横身冲突，明确不交付出图。v1源、预览与合同完整保全；v2只让抽象箭头跟随完整头部耳眼轴，所有规划点、长度和时钟相同，见 `v1-face-direction-correction.json`。

`tools/rebuild/ultraman-arc/luna-jump-resume-20261102-v1/runtime_bundle.py` 提供 `freeze`、`run`、`check-trace`。正式main适配器继承已经实跑的main装配/小JPEG/退出工具，不新建场景。冻结接口必须有 `ufeneo.arc-luna.s2.jump-whole-registered.v1` 的本人处理清单、五个action（takeoff、vertical_jump、flip_forward、flip_back、land）、各独立source/image逐SHA、二值Alpha320整图与逐像素相符atlas、共同159/根[160,280]注册合同及根实际完整画面批准。缺17独立真实源、共用旧帧或空合同均不会创建runtime候选。

未来根冻结后可在唯一Godot锁执行run，工具只在建sim前设置开局站位；随后只输单tick自然8/9/7。观察器逐tick检查模拟sprite与实际表现相、相键、位移、高度、state_tick、双顶点及完整Alpha屏内，保留实际原双方InputFrame并独立可见回放。起跳为n0/n1，空中读绝对n2..32而非重起33tick；n16/n17高136，n33..36落地，n37回idle。原输入、hash、事件、弹体和完整pair对比；用户设置/回放有保全恢复。此工具目前只做Python语法与CLI验证，未由引擎解析或实跑，不能称时钟/画面已验收。

本轮零POST、零收费、零人物候选/atlas、零Godot、零产品/共享文档/Git修改。真实基础跳跃17源、逐源人物/Alpha/严尺、共同注册和main验证仍待；追击跳、空攻与其余S2–S7另列。精确自有文件在 `subagent-owned-files-v1.json` 及配对NUL；清单自身两文件需另加。
""", encoding="utf-8", newline="\n")
    directories = [HERE, ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v1", ART, ROOT / "reports/review/2026-11-02/luna-jump-resume-guides-v1", OUT]
    owned = sorted({path for folder in directories for path in folder.rglob("*") if path.is_file()}, key=rel)
    save(OUT / "subagent-owned-files-v1.json", {"owner": "/root/luna_jump_resume", "files": [dict(path=rel(path), sha256=sha(path), bytes=path.stat().st_size) for path in owned], "also_add_manifest_itself_and_nul": True, "no_git_commit_by_subagent": True})
    (OUT / "subagent-owned-files-v1.nul").write_bytes(b"\0".join(rel(path).encode("utf-8") for path in owned) + b"\0")
    print(json.dumps({"report": rel(OUT / "README.md"), "owned_manifest": rel(OUT / "subagent-owned-files-v1.json"), "runtime_not_run": True, "POST_count": 0}, ensure_ascii=False))


if __name__ == "__main__":main()
