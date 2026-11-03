"""Shared Simplified Chinese display policy; raw source bytes remain untouched."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import re
from opencc import OpenCC

_CC = OpenCC('t2s')
# Mainland names already used by the project's reviewed character catalog.
_NAMES = {
    '超人力霸王狄奥': '提欧奥特曼', '超人力霸王OMEGA': '欧米伽奥特曼',
    '超人力霸王雷古洛斯': '雷古洛思奥特曼', '超人力霸王雷古洛思': '雷古洛思奥特曼',
    '超人力霸王涅欧斯': '奈欧斯奥特曼', '超人力霸王帕瓦德': '帕瓦特奥特曼',
    '超人力霸王马克斯': '麦克斯奥特曼', '超人力霸王梅比斯': '梦比优斯奥特曼',
    '超人力霸王迪卡': '迪迦奥特曼', '超人力霸王帝纳': '戴拿奥特曼',
    '超人力霸王杰斯': '哉阿斯奥特曼', '超人力霸王耐斯': '纳伊斯奥特曼',
    '超人力霸王雷欧': '雷欧奥特曼', '超人力霸王80': '爱迪奥特曼',
    '超人力霸王USA': '美国奥特曼', '超人力霸王R / B': '罗布奥特曼',
    '超人七号X': '赛文X奥特曼', '超人七号': '赛文奥特曼',
    '超人力霸王之父': '奥特之父', '超人力霸王之母': '奥特之母',
    '超人力霸王之王': '奥特之王',
    **{'超人力霸王' + name: name + '奥特曼' for name in ['佐菲', '杰克', '艾斯', '泰罗', '阿斯特拉', '葛雷', '迪迦', '戴拿', '盖亚', '阿古茹', '高斯', '杰斯提斯', '奈克瑟斯', '希卡利', '赛罗', '银河', '维克特利', '艾克斯', '欧布', '捷德', '罗索', '布鲁', '泰迦', '风马', '泰塔斯', '格丽乔', '利布特', '泽塔', '特利迦', '德凯', '布莱泽', '亚刻']},
    '超人力霸王': '奥特曼',
}

# Some source pages mix a translated prefix with a regional short name.
# Apply complete aliases after prefix normalization; never replace ambiguous
# human given names such as 太郎 in isolation, and never use this for identity.
_DISPLAY_ALIASES = {
    '冒牌超人': '假奥特曼', '超人五兄弟': '奥特五兄弟',
    '超人之父': '奥特之父', '超人之母': '奥特之母', '超人之王': '奥特之王',
    '赛文奥特曼上司': '赛文奥特曼的上司',
    '混沌超人灾厄': '混沌奥特曼灾厄', '混沌超人强化型': '混沌奥特曼强化型',
    '混沌超人': '混沌奥特曼',
    '异次元超人梦比优斯杀手': '梦比优斯杀手',
    '超人帝卡': '德凯奥特曼', '超人帝拿': '戴拿奥特曼',
    '超人佳亚': '盖亚奥特曼', '超人尼奥': '奈欧斯奥特曼',
    '超人Orb': '欧布奥特曼', '超人正义': '杰斯提斯奥特曼',
    '超人雅古': '亚刻奥特曼', '超人80': '爱迪奥特曼',
    '超人银河': '银河奥特曼', '超人爸爸': '奥特之父',
    '奥特曼布雷萨': '布莱泽奥特曼', '奥特曼ARC': '亚刻奥特曼',
    '奥特曼奥米加': '欧米伽奥特曼', '奥特曼德卡': '德凯奥特曼',
    '奥特曼特利卡': '特利迦奥特曼', '奥特曼杰特': '泽塔奥特曼',
    '奥特曼杰洛': '赛罗奥特曼', '奥特曼Zero': '赛罗奥特曼',
    '奥特曼杰诺': '杰诺奥特曼', '奥特曼X': '艾克斯奥特曼',
    '奥特曼卫司': '艾斯奥特曼', '奥特曼卫斯': '艾斯奥特曼',
    '奥特曼太郎': '泰罗奥特曼', '奥特曼梅比斯': '梦比优斯奥特曼',
    '奥特曼大河': '泰迦奥特曼', '超人卫司': '艾斯奥特曼',
    '超人卫斯': '艾斯奥特曼', '超人梅比斯': '梦比优斯奥特曼',
    '超人光明': '希卡利奥特曼', '超人迪加': '迪迦奥特曼',
    '超人帝纳': '戴拿奥特曼', '超人杰洛': '赛罗奥特曼',
    '超人Zero': '赛罗奥特曼', '超人X': '艾克斯奥特曼',
}

_MAINLAND_TERMS = {
    '大决战!超人8兄弟': '大决战！超奥特8兄弟',
    '大决战！超人8兄弟': '大决战！超奥特8兄弟',
    '归来的超人': '归来的奥特曼', '超人新世代之星': '奥特曼新生代之星',
    '超人10勇士': '奥特10勇士', '超人6兄弟': '奥特六兄弟',
    '超人战士': '奥特战士', '超人兄弟': '奥特兄弟',
    '超人族人': '奥特一族', '超人徽章': '奥特勋章',
    '超人五大誓言': '奥特五大誓言', '超人之钟': '奥特之钟',
    '超人之星': '奥特之星', '超人斗篷': '奥特披风',
    '超人念力': '奥特念力', '超人圆盘刃': '奥特圆盘刃',
    '超人般的力量': '超常力量', '如超人般的超能力': '超常能力',
    '超人的力量': '超常力量', '异次元超人': '异次元战士',
    '型态': '形态', '身分': '身份', '雷射': '激光',
    '公尺': '米', '公分': '厘米', '公斤': '千克', '计画': '计划',
    # 已知完整人名和道具译名先处理，再统一地区性的系列称呼。
    '咸蛋超人': '奥特曼', '超人': '奥特曼',
}


def select_chinese_variant(text):
    def variant(match):
        body = match[1]
        for lang in ['zh-cn', 'zh-hans', 'zh-tw', 'zh-hant', 'zh-hk']:
            found = re.search(r'(?:^|;)\s*' + lang + r':([^;]+)', body)
            if found:
                return found[1]
        return body
    return re.sub(r'-\{(.*?)}-', variant, text, flags=re.S)


def simplified_text(text, canonical_names=True):
    # Source links must keep their exact titles/paths, even when unescaped.
    parts = re.split(r'(https?://[^\s<>\[\]()]+)', text)
    for i in range(0, len(parts), 2):
        value = _CC.convert(parts[i])
        if canonical_names:
            for original, display in _NAMES.items():
                value = value.replace(original, display)
            for original, display in _DISPLAY_ALIASES.items():
                value = value.replace(original, display)
            for original, display in _MAINLAND_TERMS.items():
                value = value.replace(original, display)
        parts[i] = value
    return ''.join(parts)
