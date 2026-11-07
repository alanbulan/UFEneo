"""Extract Chinese entity and episode research with per-record revision provenance.

This is an evidence index, not finished gameplay data. Ambiguous names, missing
translations and unassigned forms remain in the audit instead of being invented.
"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from collections import Counter
from pathlib import Path
Path = _LayoutProjectPath
import hashlib
import json; json = _LayoutJson
import re
import unicodedata
from opencc import OpenCC
import roster.research_wikipedia as wiki
from roster.chinese_text import simplified_text
from art.paths import brief_path

ROOT = _LayoutProjectPath(_layout_root)
CC = OpenCC('t2s')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u3400-\u9fff]')
STATS = re.compile(r'身高|体重|体长|速度|握力|跳跃|年龄|配音|饰演|演员|声优|登场[话集]|首次登场|原文|台词|必杀技|音效')
GENERIC = re.compile(r'角色|人物|登场|列表|道具|装备|设计|方式|组织|战机|基地|演出|制作|概述|概要|其他|形态变化|型态变化|型态转换|故事|经历|篇章|武器|防卫|作品|地球防卫军|科学特搜队|主角|协助者|客串|关联|防卫队|电影|网路剧集|时间线|数学|政府人士|^宇宙人$|《|》|^第[\d一二三四五六七八九十]+')


def clean(raw):
    raw = re.sub(r'<ref\b[^>]*(?:/>|>.*?</ref\s*>)', '', raw, flags=re.S | re.I)
    def variant(match):
        content = match[1]
        for lang in ['zh-cn', 'zh-hans', 'zh-tw', 'zh-hant', 'zh-hk']:
            found = re.search(r'(?:^|;)\s*' + lang + r':([^;]+)', content)
            if found:
                return found[1]
        return content
    raw = re.sub(r'-\{(.*?)}-', variant, raw, flags=re.S)
    raw = re.sub(r'<(?:br|hr)\s*/?>', '\n', raw, flags=re.I)
    raw = re.sub(r'\[\[(?:File|Image|文件|檔案):[^\n]*', '', raw, flags=re.I)
    text = CC.convert(wiki.plain(raw)).strip()
    for original, simplified in [('獣','兽'),('戦','战'),('団','团'),('悪','恶'),('実','实'),('沢','泽'),('姫','姬')]:
        text = text.replace(original, simplified)
    return text


def key(text):
    return re.sub(r'[\s·・、/\-：:（）()《》「」\[\]，,。]', '', unicodedata.normalize('NFKC', CC.convert(text))).lower()


def short_name(raw):
    text = clean(raw).strip("*;:' \n")
    text = re.split(r'[（(\n]|又译|又称', text)[0].strip(" '）)")
    text = re.sub(r'^(?:又称|又译|别名)[：:]?', '', text).strip()
    return text


def is_name(text):
    return 1 < len(text) <= 48 and not re.search(r'[。！!？?：:;；=]|https?://', text) and not STATS.search(text)


def chinese_excerpt(text):
    text = clean(text)
    text = re.sub(r'[（(][^（）()\n]*[\u3040-\u30ff][^（）()\n]*[）)]', '', text)
    lines = [line.strip(' :*') for line in text.splitlines()
             if HAN.search(line) and not KANA.search(line) and not line.strip().startswith(('原文：','台词：'))]
    return '\n'.join(lines)


def blocks(raw):
    parts = re.split(r'(?m)^(={2,6})\s*(.*?)\s*\1\s*$', raw)
    stack = []
    for i in range(1, len(parts), 3):
        level, heading, body = len(parts[i]), clean(parts[i + 1]), parts[i + 2]
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))
        yield level, heading, ' / '.join(h for _, h in stack), body


def split_cells(text):
    """Split wikitable cells without splitting pipes inside templates/links."""
    pieces, current, depth = [], [], 0
    i = 0
    while i < len(text):
        pair = text[i:i+2]
        if pair in ['{{', '[[']:
            depth += 1
        elif pair in ['}}', ']]']:
            depth = max(0, depth - 1)
        if pair in ['||', '!!'] and not depth:
            pieces.append(''.join(current)); current = []; i += 2; continue
        current.append(text[i]); i += 1
    pieces.append(''.join(current))
    return pieces


def table_rows(raw):
    for table in re.findall(r'(?ms)^\{\|[^\n]*\n(.*?)^\|}', raw):
        spans = {}
        output = []
        for row in re.split(r'(?m)^\|-[^\n]*\n', table):
            cells = []
            for line in row.splitlines():
                if line.startswith(('|+', '{|', '|}')):
                    continue
                if line.startswith(('!', '|')):
                    cells.extend(split_cells(line[1:]))
                elif cells:
                    cells[-1] += '\n' + line
            if not cells:
                continue
            expanded = {}
            for col in list(spans):
                value, remaining = spans[col]
                expanded[col] = value
                if remaining <= 1:
                    del spans[col]
                else:
                    spans[col] = (value, remaining - 1)
            col = 0
            for cell in cells:
                while col in expanded:
                    col += 1
                prefix = cell.split('|', 1)[0]
                attrs = '=' in prefix and not any(mark in prefix for mark in ['{{', '[['])
                value = cell.split('|', 1)[1] if attrs and '|' in cell else cell
                r = re.search(r'rowspan\s*=\s*["\']?(\d+)', prefix) if attrs else None
                c = re.search(r'colspan\s*=\s*["\']?(\d+)', prefix) if attrs else None
                width = int(c[1]) if c else 1
                for offset in range(width):
                    expanded[col + offset] = value
                    if r and int(r[1]) > 1:
                        spans[col + offset] = (value, int(r[1]) - 1)
                col += width
            output.append([expanded.get(i, '') for i in range(max(expanded, default=-1) + 1)])
        yield output


def extract():
    seed = json.loads((ROOT / 'content/roster/series.json').read_text(encoding='utf-8'))
    works = {x['id']: x for x in seed['series']}
    sources = json.loads((ROOT / 'docs/research/wikipedia/index.json').read_text(encoding='utf-8'))['pages']
    entities, episodes, audit = [], [], []
    work_titles = {}
    for source in sources:
        if source['id'].startswith('series_'):
            for title in [source.get('title', ''), source['requested_title']]:
                work_titles[key(title)] = source['target']

    def emit(raw_name, kind, source, heading, text='', base='', targets=None, method='named_entry'):
        name = short_name(raw_name)
        if not is_name(name) or GENERIC.fullmatch(name) or name in ['超古代怪兽','幻影怪兽军团','兽人']:
            return
        target_ids = [x for x in (targets or source['targets']) if x in works]
        evidence = {'source': source['id'], 'heading': heading, 'revision_url': source['revision_url'], 'method': method}
        aliases = []
        for template in wiki.mwparserfromhell.parse(raw_name).filter_templates():
            if re.fullmatch(r'nihongo\d*', str(template.name).strip(), re.I):
                for p in template.params:
                    aliases.extend(piece.strip() for piece in re.split(r'[/／]', clean(str(p.value))))
        name_markup = re.split(r'[（(]', raw_name)[0]
        name_markup = re.sub(r'<ref\b[^>]*(?:/>|>.*?</ref\s*>)', '', name_markup, flags=re.S|re.I)
        aliases += [str(link.title) for link in wiki.mwparserfromhell.parse(name_markup).filter_wikilinks(recursive=False)]
        for original_line in re.findall(r'(?m)^[:*]?\s*原文[^\n]*', text):
            for template in wiki.mwparserfromhell.parse(original_line).filter_templates():
                if str(template.name).strip().lower() == 'lang' and template.has(2):
                    aliases.append(clean(str(template.get(2).value)))
        aliases = list(dict.fromkeys(alias for alias in aliases if alias.strip()))
        rec = {'name': name, 'original': clean(raw_name), 'aliases': aliases, 'kind': kind, 'series_ids': target_ids,
               'base_hint': base, 'text': clean(text)[:3500], 'evidence': evidence}
        if not target_ids or KANA.search(name) or not HAN.search(name):
            rec['reason'] = 'work_or_chinese_name_requires_review'
            audit.append(rec)
        else:
            entities.append(rec)

    for source in sources:
        raw_path = ROOT / '.references/wikipedia' / (source['id'] + '.wiki')
        if source['status'] != 'fetched' or source['language'] != 'zh' or not raw_path.exists():
            continue
        raw = raw_path.read_text(encoding='utf-8')
        subject_kind = 'kaiju' if source['id'] in ['character_zh_gomora','character_zh_zetton'] else 'hero'
        subject = source.get('title','') if source['id'].startswith('character_zh_') else ''
        if subject:
            emit(subject, subject_kind, source, '角色资料', raw.split('\n==')[0], method='character_article')
        hero_hint = ''
        for level, heading, context, body in blocks(raw):
            if re.search(r'超人力霸王|奥特曼|超人七号', heading) and not GENERIC.search(heading):
                hero_hint = heading
            elif level == 2:
                hero_hint = ''
            if subject:
                hero_hint = subject
                if re.search(r'必杀|技能|能力|经历|故事',heading):
                    emit(subject, subject_kind, source, context, body, method='ability_section')
            forms = bool(re.search(r'型态|形态|型式', context)) and not re.search(r'技能|必杀|能力|武器', context)
            monster = bool(re.search(r'(?:登场|本作).*怪兽|怪兽.*列表|宇宙人|宇宙怪兽', context)) or '怪獸列表' in source.get('title', '')
            human = bool(re.search(r'登场(?:角色|人物)|主角|^角色|角色列表', context)) and not monster and not forms
            if source['id'].startswith('series_') and level >= 3 and re.fullmatch(r'(?:超人力霸王.{0,16}|超人七号.{0,4})',heading) and not GENERIC.search(heading) and not heading.endswith('的宇宙'):
                emit(heading, 'hero', source, context, body, method='character_heading')
            if hero_hint and re.search(r'必杀技|技能',heading):
                emit(hero_hint, 'hero', source, context, body, method='ability_section')
            if '怪獸列表' in source.get('title', '') and level == 2 and not GENERIC.search(heading):
                emit(heading, 'kaiju', source, context, body, method='dedicated_heading')
            # Definition/bullet entries, with their descriptions up to the next entry.
            matches = list(re.finditer(r'(?m)^[;*]\s*([^\n]+)', body))
            for n, match in enumerate(matches):
                line = match[1]
                name = short_name(line)
                description = body[match.end():matches[n+1].start() if n+1 < len(matches) else len(body)]
                if not is_name(name) or GENERIC.search(name) or len(name) > 36:
                    continue
                if forms and ("'''" in line or re.search(r'{{nihongo|型|模式|装甲|形态', line)):
                    emit(line, 'form', source, context, description, hero_hint)
                elif monster and ("'''" in line or '{{nihongo' in line or match[0].startswith(';')):
                    kind = 'story' if source['id'].startswith('related_') and not re.search(r'怪兽|星人|超兽|巨人|机甲|宇宙人|魔人', name) else 'kaiju'
                    emit(line, kind, source, context, description)
                elif human and match[0].startswith(';') and not re.search(r'演员|声优|饰演|配音|资料|剧情|其他|^客串', name):
                    emit(line, 'story', source, context, description)
            if not source['id'].startswith('master_'):
                continue
        for table in table_rows(raw):
            columns = {}
            for cells in table:
                header = [clean(c) for c in cells]
                if any(re.fullmatch(r'集数|话数', c.strip()) for c in header) and any(re.search(r'怪兽|超兽|登场.*宇宙人', c) for c in header):
                    columns = {tag: next((i for i,c in enumerate(header) if re.search(pattern,c)), -1)
                               for tag,pattern in [('kaiju',r'怪兽|超兽|宇宙人'),('episode',r'集数|话数'),('title',r'标题|名称|题名')]}
                    continue
                if source['id'] == 'master_heroes':
                    if not cells or not "'''" in cells[0]:
                        continue
                    targets = []
                    if len(cells) > 1:
                        for title in re.findall(r'\[\[([^\]|#]+)', cells[1]):
                            if key(title) in work_titles:
                                targets.append(work_titles[key(title)])
                    emit(cells[0], 'hero', source, '英雄总表', '\n'.join(cells[:4]), targets=targets or ['galaxy_fight'], method='master_table')
                elif columns and len(cells) > columns['kaiju'] >= 0:
                    index = columns['episode']
                    ep = short_name(cells[index]) if len(cells) > index >= 0 else ''
                    index = columns['title']
                    title_raw = cells[index] if len(cells) > index >= 0 else ''
                    title_parts = clean(title_raw).splitlines()
                    title = next((p for p in reversed(title_parts) if HAN.search(p) and not KANA.search(p)), '')
                    names = []
                    for line in re.split(r'<br\s*/?>|\n', cells[columns['kaiju']], flags=re.I):
                        name = short_name(line)
                        if is_name(name) and not GENERIC.search(name) and name not in names:
                            emit(line, 'kaiju', source, '播映表 / 第' + ep + '集', targets=source['targets'], method='episode_table')
                            names.append(name)
                    if ep and re.fullmatch(r'(?:\d+(?:\.\d+)?|SP\d*)', ep, re.I):
                        episodes.append({'series_ids': [x for x in source['targets'] if x in works], 'number': ep,
                                         'title': title or '第' + ep + '集', 'monster_names': names,
                                         'source': source['id'], 'revision_url': source['revision_url'], 'status': 'research_only'})
    unique = {}
    for entity in entities:
        fingerprint = (entity['kind'], key(entity['base_hint']), key(entity['name']), tuple(entity['series_ids']),entity['evidence']['heading'])
        if fingerprint not in unique or len(entity['text']) > len(unique[fingerprint]['text']):
            unique[fingerprint] = entity
    result = {'schema': 1, 'license': wiki.LICENSE, 'entities': list(unique.values()), 'episodes': episodes,
              'unresolved': audit, 'scope_note': '当前已抓取维基页面的命名条目与播映表；不表示整个系列资料已经齐全。'}
    (ROOT / 'content/roster/wiki-extracted.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'entities':len(unique),'kinds':Counter(x['kind'] for x in unique.values()),'episodes':len(episodes),'unresolved':len(audit)},ensure_ascii=False))
    return result


if __name__ == '__main__':
    extract()


REGIONAL = {'迪卡':'迪迦','迪加':'迪迦','帝纳':'戴拿','帝拿':'戴拿','梅比斯':'梦比优斯','雷欧斯':'奈欧斯',
            '纳克斯':'奈克瑟斯','特利卡':'特利迦','杰洛':'赛罗','杰特':'泽塔','卫司':'艾斯','太郎':'泰罗',
            '尊王':'奥特之王','大河':'泰迦','布雷萨':'布莱泽','雅古':'亚刻','雷克洛斯':'雷古洛思',
            '正义':'杰斯提斯','雷杰':'雷杰多','令河':'令迦','亚格':'阿古茹','帝纳斯':'戴纳斯',
            '哥摩拉':'哥莫拉','绝顿':'杰顿','皮古蒙':'皮古蒙','匹咕蒙':'皮古蒙','温达姆':'乌英达姆',
            '电王兽':'艾雷王','艾雷金刚':'艾雷王','内隆嘎':'内隆嘎','内隆刚':'内隆嘎','尼隆加':'内隆嘎',
            '古维拉':'古比拉','安特拉':'安东拉','红王':'雷德王','布雷萨':'布莱泽','德卡':'德凯',
            '奥米加':'欧米伽','乔伊尼亚斯':'乔尼亚斯','泰坦斯':'泰塔斯','雷古洛斯':'雷古洛思','帕瓦德':'帕瓦特'}


def localize(text):
    text = clean(text)
    for original in sorted(REGIONAL, key=len, reverse=True):
        text = text.replace(original, REGIONAL[original])
    # Keep real proper names; only normalize the franchise naming convention.
    text = re.sub(r'女?超人力霸王([A-Za-z\u3400-\u9fff0-9 ]+)', lambda m: m[1].strip() + '奥特曼', text)
    for original, translated in {'之父奥特曼':'奥特之父','之母奥特曼':'奥特之母','80奥特曼':'爱迪奥特曼',
            'X奥特曼':'艾克斯奥特曼','THE NEXT奥特曼':'奈克斯特奥特曼','胜利奥特曼':'维克特利奥特曼',
            '银河胜利奥特曼':'银河维克特利奥特曼','影子奥特曼':'夏德奥特曼','男孩奥特曼':'博伊奥特曼',
            'Blazar奥特曼':'布莱泽奥特曼','ARC奥特曼':'亚刻奥特曼','King Joe':'金古桥','Exceed 艾克斯奥特曼':'艾克斯奥特曼超越型'}.items():
        text = text.replace(original, translated)
    return text


def identity_key(text):
    text = localize(text)
    text = text.replace('超人七号', '赛文奥特曼').replace('超人赛文', '赛文奥特曼')
    return key(text.replace('奥特曼','').replace('超人力霸王','').replace('型态','形态'))


def bare_name(text):
    text = localize(text)
    if ' ' in text and HAN.search(text.split()[-1]):
        return text.split()[-1]
    # A classifier is removable only when a proper name follows it.
    return re.sub(r'^.{0,12}?(?:怪兽|超兽|恐龙|机器人|宇宙人|宇宙忍者|怪人|珍兽|原人|海兽|油兽|魔神|战士|勇士|斗士|策士)\s*(?=.{2})', '', text)


def merge(entries, series, extracted, wiki_sources):
    """Merge clear identities; retain ambiguous entities and translations in audit."""
    work_by_id = {w['id']:w for w in series}
    seed = json.loads((ROOT/'content/roster/series.json').read_text(encoding='utf-8'))
    hero_by_work = {w['id']:w['heroes'][0].split('|')[0] for w in seed['series'] if w['heroes']}
    aliases = {}

    def remember(alias, cid):
        # Removing the franchise prefix can leave an empty identity. Empty
        # template parameters must never become a wildcard for that character.
        for probe in {identity_key(alias), identity_key(bare_name(alias))}:
            if probe and cid not in aliases.setdefault(probe, []):
                aliases[probe].append(cid)

    for row in entries.values():
        for alias in [row['name'], *row['aliases']]:
            remember(alias, row['id'])
        if row['kind'] == 'form':
            remember(row['id'].split('__')[-1].replace('_',' '), row['id'])
    for source in wiki_sources:
        wid = source['id'].removeprefix('series_')
        if source['id'].startswith('series_') and wid in hero_by_work:
            remember(source.get('title',''), hero_by_work[wid])
    pending, imported, matched = [], [], 0
    for entity in extracted['entities']:
        name, kind = localize(entity['name']), entity['kind']
        wid = entity['series_ids'][0] if len(entity['series_ids']) == 1 else ''
        generic_hero = entity['name'] in ['超人力霸王', '初代超人力霸王', '超人力霸王/利琵亚']
        # Mixed hero/monster sections may classify the film's Ultraman as a
        # kaiju. Resolve the named lead using its work before global aliases.
        if generic_hero and entity['evidence']['source'] == 'series_' + wid and wid in hero_by_work:
            kind = 'hero'
        if '石像A、B' in name:
            pending.append(entity | {'reason':'unnamed_statues_not_individual_heroes'}); continue
        base = ''
        if kind == 'form':
            base_options = aliases.get(identity_key(entity['base_hint']), [])
            base_options = [x for x in base_options if entries[x]['kind'] in ['hero','dark_ultra']]
            if len(set(base_options)) == 1:
                base = base_options[0]
            elif not entity['base_hint'] and len(entity['series_ids']) == 1:
                base = hero_by_work.get(entity['series_ids'][0], '')
            if not base:
                pending.append(entity | {'reason':'form_parent_requires_review'}); continue
        probes = [name, bare_name(name), *entity.get('aliases', [])]
        compatible = ['hero','dark_ultra'] if kind == 'hero' else [kind]
        options = []
        for probe in probes:
            if not identity_key(probe):
                continue
            options.extend(cid for cid in aliases.get(identity_key(probe), []) if entries[cid]['kind'] in compatible
                           and (kind != 'form' or entries[cid]['base_character'] == base))
            if kind in ['story','kaiju']:
                options.extend(cid for cid in aliases.get(identity_key(probe), []) if entries[cid]['kind'] in ['hero','dark_ultra'])
        # Match form labels separately from the full character name.
        if kind == 'form' and not options:
            for row in entries.values():
                if row['kind'] == 'form' and row['base_character'] == base:
                    label = row['name'].split('·')[-1].strip()
                    normalize_form = lambda s: re.sub(r'形态$|模式$|型$', '', identity_key(re.split(r'[（(]',s)[0]))
                    synonyms = {'力量':'强力','天空':'空中','皇家至尊':'尊皇','究极终结':'终极最终','烈焰爆燃':'刚燃',
                                '顶尖极速':'机敏','崇高':'豪勇','阿尔法锋刃':'阿尔法装甲','贝塔粉碎':'贝塔冲击',
                                '德尔塔升华钩爪':'德尔塔天爪','火':'烈火','水':'跃水','风':'旋风','土':'大地'}
                    candidate = normalize_form(name)
                    if normalize_form(label) == synonyms.get(candidate,candidate):
                        options.append(row['id'])
        options = list(dict.fromkeys(options))
        # A generic name is not enough to collapse separate film universes.
        if kind == 'hero' and generic_hero:
            if wid in hero_by_work and (entity['evidence']['source'] in ['series_'+wid,'master_heroes','character_zh_ultraman']):
                options = [hero_by_work[wid]]
        if len(options) > 1:
            # Repeated official work cards retain incarnations, but can share a
            # sourced Chinese name. Prefer the card for this work for the note.
            for cid in options:
                if KANA.search(entries[cid]['name']):
                    entries[cid]['aliases'].append(entries[cid]['name'])
                    entries[cid]['name'] = name
                    entries[cid].pop('name_note',None)
            options.sort(key=lambda cid: (not any(wid in entries[cid]['series_ids'] for wid in entity['series_ids']),
                                          not entries[cid]['identity_evidence'].startswith('official_'), cid.startswith('wiki_'), cid))
        if options:
            row = entries[options[0]]; matched += 1
            if KANA.search(row['name']):
                row['aliases'].append(row['name']); row['name'] = name
                row.pop('name_note',None)
        else:
            wid = entity['series_ids'][0]
            work = work_by_id[wid]
            cid = 'wiki_' + hashlib.sha256((kind+'|'+base+'|'+identity_key(bare_name(name))).encode()).hexdigest()[:14]
            if cid in entries:
                row = entries[cid]
            else:
                if kind == 'hero' and re.search(r'黑暗|邪恶|卡蜜拉|达拉姆|希特拉|卡尔蜜拉|达贡|希特拉姆',name):
                    kind = 'dark_ultra'
                label = entries[base]['name'] + ' · ' + name if base else (bare_name(name) if kind == 'kaiju' else name)
                row = {'id':cid,'name':label,'kind':kind,'era':work['era'],'series_ids':[],
                       'catalog_year':work['year'],'aliases':[],'base_character':base,'fusion_components':[],
                       'identity_evidence':'wikipedia_named_record','association_evidence':'revision_linked_wikipedia',
                       'sources':[],'official_url':'','playable':False,'fighter_resource':'',
                       'production_stage':'identity_research','brief':brief_path(cid, kind)}
                if base:
                    row['form_kind'] = 'combat_form_to_research'
                entries[cid] = row; imported.append(cid)
        for alias in [entity['name'], *entity.get('aliases', [])]:
            if alias.strip() and alias not in row['aliases']:
                row['aliases'].append(alias)
            remember(alias, row['id'])
        for wid in entity['series_ids']:
            if wid not in row['series_ids']:
                row['series_ids'].append(wid)
        notes = row.setdefault('research_notes', [])
        note = {'heading':simplified_text(clean(entity['evidence']['heading'])),'text':simplified_text(chinese_excerpt(entity['text']))[:2000],
                'revision_url':entity['evidence']['revision_url'],'source':entity['evidence']['source'],
                'method':entity['evidence']['method']}
        if note not in notes:
            notes.append(note)
    # Resolve current official Japanese-only cards by their observed Japanese aliases.
    for row in entries.values():
        if row.get('research_notes'):
            order = {'ability_section':0,'character_article':1,'character_heading':2,'named_entry':3,'dedicated_heading':3,'master_table':4,'episode_table':5}
            row['research_notes'].sort(key=lambda n:(order.get(n['method'],6), -len(n['text']), n['source'], n['heading']))
        if KANA.search(row['name']):
            row['chinese_name_pending'] = True
    return {'imported_ids':imported,'matched_records':matched,'pending':pending,
            'source_unresolved':len(extracted['unresolved'])}
