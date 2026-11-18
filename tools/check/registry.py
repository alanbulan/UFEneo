"""tools/check 全部检查门脚本的唯一注册表。

约定：
- tools/check/ 下所有独立检查脚本（除本模块外）必须在此登记；
- mode == "verify" 表示随 tools/verify.py 默认全量回归执行；
- mode == "authoring_gate" 表示制作期或专项诊断门，不阻断日常纯代码回归。
"""
from __future__ import annotations

CHECKS: dict[str, dict[str, str]] = {
    "gdscript_warnings": {
        "mode": "verify",
        "module": "check.gdscript_warnings",
        "summary": "GDScript 全仓静态警告零容忍扫描（只读校验 project.godot 严格警告）",
    },
    "layering": {
        "mode": "verify",
        "module": "check.layering",
        "summary": "六层单向依赖、禁止引用 tests、core 确定性与 presentation 只读守卫",
    },
    "seven_demo_pipeline": {
        "mode": "verify",
        "module": "check.seven_demo_pipeline",
        "summary": "赛文示范流水线数据门（走路等长、受击硬直覆盖、命中框比例）",
    },
    "catalogue_references": {
        "mode": "verify",
        "module": "check.catalogue_references",
        "summary": "图鉴参考图来源格式、分辨率与元数据一致性检查",
    },
    "audio_manifest": {
        "mode": "verify",
        "module": "check.audio_manifest",
        "summary": "运行时音频清单路径、PCM 规格与响度一致性检查",
    },
    "fx_audio": {
        "mode": "verify",
        "module": "check.fx_audio",
        "summary": "音频来源台账 SHA/峰值与阶段三特效图集校验",
    },
    "pixel_ui": {
        "mode": "verify",
        "module": "check.pixel_ui",
        "summary": "正式 UI 禁程序绘制装饰与九宫格/像素字体资源门禁",
    },
    "catalogue_idle": {
        "mode": "verify",
        "module": "check.catalogue_idle",
        "summary": "图鉴待机动画条画布尺寸、二值 Alpha、站高与帧差分体检",
    },
    "catalogue_facing": {
        "mode": "authoring_gate",
        "module": "check.catalogue_facing",
        "summary": "图鉴轮廓翻转 IoU 启发式正面朝向排查",
    },
    "frame_scale_jumps": {
        "mode": "authoring_gate",
        "module": "check.frame_scale_jumps",
        "summary": "已装动画逐帧人物尺度突变检测与定锚修复",
    },
    "sprite_quality": {
        "mode": "authoring_gate",
        "module": "check.sprite_quality",
        "summary": "通用精灵像素硬门（辉光门/二值 Alpha/孤岛/≤32 色/站姿高差/走路等长位移）",
    },
}


def registered_stems() -> set[str]:
    return set(CHECKS.keys())


def verify_stems() -> list[str]:
    return [name for name, meta in CHECKS.items() if meta.get("mode") == "verify"]
