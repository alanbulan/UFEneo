"""保全v1：只改完整抽象头部朝向箭头，跟随耳眼轴旋转；不变人物或规划比例。"""
from pathlib import Path
import importlib.util
import math
import sys

sys.dont_write_bytecode = True
from PIL import ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("luna_jump_resume_first_guide_tool", HERE / "prepare_guides.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
g = m.g
m.ART = m.ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v2"
m.OUT = m.ROOT / "reports/review/2026-11-02/luna-jump-resume-guides-v2"


def make_whole_abstract_guide(path, points, title, note):
    image = g.build_layout_guide(1, 1, 1024, 1024, 48, 48).convert("RGB")
    image.paste((100, 112, 128), (0, 0, 1024, 1024))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(g.FONT, 21)
    small = ImageFont.truetype(g.FONT, 18)
    draw.text((48, 12), title, fill="white", font=font)
    draw.text((48, 43), "完整新抽象姿态：白=近亮左肢；暗=远暗右肢；绝非最终人物", fill="#ffe780", font=small)
    for line, start in enumerate(range(0, len(note), 22)):
        draw.text((48, 104 + line * 25), note[start:start + 22], fill="#ffe780", font=small)
    draw.line((56, 960, 968, 960), fill="#b6c5d4", width=2)
    draw.text((52, 986), "虚拟注册根 [512,960]；不等于空中人物的实际地面，不画进最终PNG", fill="white", font=small)
    at = lambda key: g.xy(points[key])
    draw.polygon([at(k) for k in ["near_shoulder", "far_shoulder", "far_hip", "near_hip"]], fill="#647f82", outline="#57e2da", width=4)
    for side, color in [("far", "#242424"), ("near", "#ffffff")]:
        for chain in [["_hip", "_knee", "_ankle", "_toe"], ["_shoulder", "_elbow", "_wrist", "_fist"]]:
            draw.line([at(side + suffix) for suffix in chain], fill=color, width=15, joint="curve")
        for suffix in ["_hip", "_knee", "_ankle", "_shoulder", "_elbow", "_wrist"]:
            x, y = at(side + suffix)
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color)
        for suffix, radius in [("_wrist", 20), ("_fist", 15)]:
            x, y = at(side + suffix)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=color, width=3)
    draw.line([at(k) for k in ["hip_center", "neck_base"]], fill="#57e2da", width=11)
    draw.line([at("neck_base"), at("chin")], fill="#57e2da", width=7)
    skull, chin = points["skull_top"], points["chin"]
    mid = [(skull[0] + chin[0]) / 2, (skull[1] + chin[1]) / 2]
    delta = g.sub(chin, skull)
    major = math.dist(chin, skull) / 2
    direction = [delta[0] / (major * 2), delta[1] / (major * 2)]
    perpendicular = [-direction[1], direction[0]]
    outline = []
    for n in range(49):
        t = n * math.tau / 48
        outline.append(g.xy([mid[0] + math.cos(t) * major * direction[0] + math.sin(t) * major * 0.68 * perpendicular[0], mid[1] + math.cos(t) * major * direction[1] + math.sin(t) * major * 0.68 * perpendicular[1]]))
    draw.line(outline, fill="#ffe780", width=5)
    for name in ["skull_top", "chin"]:
        x, y = at(name)
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#ffe780")
    # 由当前完整头部的耳→眼方向画箭头；倒立/横身绝不再固定朝屏幕右。
    ex, ey = at("eye")
    dx, dy = g.sub(points["eye"], points["ear"])
    norm = math.hypot(dx, dy)
    dx, dy = dx / norm, dy / norm
    nx, ny = -dy, dx
    start, end = (ex + 12 * dx, ey + 12 * dy), (ex + 58 * dx, ey + 58 * dy)
    draw.line([start, end], fill="#ffe780", width=5)
    draw.polygon([end, (end[0] - 15 * dx + 9 * nx, end[1] - 15 * dy + 9 * ny), (end[0] - 15 * dx - 9 * nx, end[1] - 15 * dy - 9 * ny)], fill="#ffe780")
    x, y = g.xy([128, 248])
    draw.line((x - 10, y, x + 10, y), fill="#ff9f72", width=3)
    draw.line((x, y - 10, x, y + 10), fill="#ff9f72", width=3)
    assert not path.exists()
    image.save(path)
    return image


if __name__ == "__main__":
    g.make_guide = make_whole_abstract_guide
    m.main()
    first = m.ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v1/jump-resume-contract.json"
    old = m.read(first)
    current = m.read(m.ART / "jump-resume-contract.json")
    for before, after in zip(old["new_air_guide_briefs_for_root_review"], current["new_air_guide_briefs_for_root_review"]):
        a, b = m.read(m.ROOT / before["pose_target"]["path"]), m.read(m.ROOT / after["pose_target"]["path"])
        assert a == b  # 全部姿态点、长度和时钟不变。
    m.save(m.OUT / "v1-face-direction-correction.json", {"preserved_first_contract": m.ref(first), "new_contract": m.ref(m.ART / "jump-resume-contract.json"), "observed_v1_issue": "十三张新air guide复用旧ground helper；眼部方向箭头固定朝屏幕右，横身/倒立时与完整头部朝向冲突，不能交根用于出图。", "v2_change": "只重画抽象朝向箭头，使其跟随当前完整头部耳眼轴；人物像素仍零，全部姿态点/共同159规划/时钟完全相同。", "v1_not_submitted_or_person_source": True, "POST_count": 0, "Godot_started": False})
