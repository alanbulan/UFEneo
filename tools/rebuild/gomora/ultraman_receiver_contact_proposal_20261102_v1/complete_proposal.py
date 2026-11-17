"""补充完整2倍配对、05→本人倒立0接续及最小通用依赖；零运行资源写入。"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import propose as p

MOVE=p.ROOT/'reports/review/2026-11-02/gomora-super3-resume-front-v1/product/content/fighters/gomora/moves/special3.json'
MANIFEST=p.ROOT/'reports/review/2026-11-02/gomora-super3-resume-front-v1/product/assets/fighters/gomora/animations/manifest.json'
BASE=p.REPORT/'proposal-v1/precise-contact-and-canvas-proposal.json'
OUT=p.REPORT/'continuation-and-dependency-v1'


def discard_target_values(text):
    """在JSON建对象前，按字符串/配对括号扫描跳过整个target值，绝不解码其中坐标。"""
    out=[];i=0
    def string_end(start):
        j=start+1
        while j<len(text):
            if text[j]=='\\':j+=2;continue
            if text[j]=='"':return j+1
            j+=1
        raise ValueError('unterminated JSON string')
    while i<len(text):
        if text[i]!='"':out.append(text[i]);i+=1;continue
        end=string_end(i);token=text[i:end];j=end
        while j<len(text) and text[j].isspace():j+=1
        if json.loads(token)!='target' or text[j]!=':':out.append(token);i=end;continue
        j+=1
        while text[j].isspace():j+=1
        assert text[j]=='{'
        level=0;k=j
        while k<len(text):
            if text[k]=='"':k=string_end(k);continue
            if text[k] in '[{':level+=1
            elif text[k] in ']}':
                level-=1
                if level==0:k+=1;break
            k+=1
        assert level==0
        out.append(text[i:j]);out.append('null');i=k
    return ''.join(out)


def non_target_timing():
    move=json.loads(discard_target_values(MOVE.read_text('utf-8-sig')))
    clip=p.read(MANIFEST)['clips']['special3']
    order=clip['source_phase_order']
    assert order==[0,1,2,3,4,5,6,7,9,8,10,11,12,13,14,15,16,17]
    whitelist=['sprite','dx','dy','throw_height']
    rows=[]
    for raw in range(20,48):
        frame=move['frames'][raw];assert frame['target'] is None
        row={'raw_tick':raw,**{k:frame[k] for k in whitelist if k in frame}}
        row['actor_source_phase']=order[frame['sprite']]
        row['throw_height_present']='throw_height' in frame
        rows.append(row)
    assert all(r['dx']==0 and r['dy']==0 and not r['throw_height_present'] for r in rows)
    return {'move_source':p.rec(MOVE),'actor_clip_source':p.rec(MANIFEST),
        'target_values_lexically_skipped_before_json_object_construction':True,
        'consumed_frame_fields':whitelist,'actor_source_order':order,'raw20_to47_non_target_rows':rows,
        'raw43_actor_source_phase':10,'raw44_actor_source_phase':11,
        'throw_height_raw43':None,'throw_height_raw44':None,
        'simulation_dependency':[p.rec(p.ROOT/'core/combat/throw_resolver.gd'),p.rec(p.ROOT/'core/combat/match_director.gd')],
        'static_height_reason':'20–47无throw_height；配对投期间match_director不施加普通重力，throw_resolver无该字段不改actor.height。候选代码意图为H43=H44=捕获后高度H；仍需正式main的真实状态证据。',
        'actual_main_or_trace_verified':False}


def scene(actor,receiver,origin,color,marked=False,rpoint=None):
    im=Image.new('RGBA',(640,384),color)
    im.alpha_composite(actor,(64,64));im.alpha_composite(receiver,(64+origin[0],64+origin[1]))
    if marked:
        d=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',14)
        x,y=rpoint[0]+64,rpoint[1]+64
        d.ellipse((x-4,y-4,x+4,y+4),outline='#ffdf60',width=1)
        d.text((x+6,y-18),'R pelvis estimate',font=font,fill='#ffdf60',stroke_width=1,stroke_fill='black')
        d.line((0,368,639,368),fill='#677080')
    return im.convert('RGB')


def scene_page(im,path,text):
    enlarged=im.resize((1280,768),Image.Resampling.NEAREST)
    page=Image.new('RGB',(1280,836),'#30343d');page.paste(enlarged,(0,68))
    d=ImageDraw.Draw(page);font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',18)
    d.text((12,8),text,font=font,fill='white')
    d.text((12,35),'完整640×384场景精确2倍；仅整图平移、无PNG注册，非正式游戏截图。',font=font,fill='white')
    return p.jpeg(page,path)


def continuation_page(prev,next_,path,color,label,marked,rpoint):
    page=Image.new('RGB',(744,1030),'#30343d');d=ImageDraw.Draw(page)
    font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',17)
    d.text((12,8),'初代05 → 本人现装thrown_back[0] / 完整人物接续提案',font=font,fill='white')
    d.text((12,34),'骨盆R是推定参照；R不跳不代表头/手/背棘遮挡及整人连续性已通过。',font=font,fill='white')
    for top,im,title in [(98,prev,'raw40–43：哥莫拉源10＋初代新05'),(546,next_,'raw44–47：哥莫拉源11＋本人既有倒立0完整格')]:
        d.text((12,top-28),f'{label} / {title}',font=font,fill='white')
        page.paste(im,(52,top))
    d.text((12,946),'提案root：新05 [-30,89] → 倒立0 [-33,99]；相对根位移[-3,+10]。',font=font,fill='white')
    d.text((12,974),f'R在哥莫拉完整画布为{rpoint}；仅H43=H44时R局部差[0,0]，合计误差±11px。',font=font,fill='white')
    d.text((12,1002),'raw44无throw_height；保持既有抛出/撞地时序，真实main、双向与回放尚待。',font=font,fill='white')
    return p.jpeg(page,path)


def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    rows,before=p.source_rows();base=p.read(BASE);manual=p.read(p.ROOT/base['manual_points']['path'])
    by_id={r['id']:r for r in manual['sources']}
    nxt=p.next_actor_row();before[nxt['image']['path']]=nxt['image']['sha256']
    before.update({str(q.relative_to(p.ROOT)).replace('\\','/'):p.sha(q) for q in [MOVE,MANIFEST,BASE]})
    timeline=non_target_timing();p.save(OUT/'non-target-raw43-to44-timing.json',timeline)
    pages=[]
    for pair in base['pairs']:
        actor=p.picture(by_id[f"actor-{pair['actor_source_phase']:02d}"])
        receiver=p.picture(by_id[f"receiver-{pair['phase']:02d}"])
        im=scene(actor,receiver,pair['whole_179_display_origin_in_actor_canvas'],'#252b35')
        pages.append(scene_page(im,OUT/f"phase{pair['phase']:02d}-complete-scene-2x-dark.jpg",f"phase{pair['phase']:02d} / 哥莫拉{pair['actor_source_phase']:02d}＋初代179 / 完整配对"))
    pair=base['pairs'][5];continuation=base['thrown_back0_continuation'];rpoint=pair['receiver_R_in_actor_canvas']
    assert rpoint==[225,122] and continuation['next_thrown_back0_full_cell_origin']==[127,21]
    prev_actor=p.picture(by_id['actor-10']);prev_receiver=p.picture(by_id['receiver-05'])
    next_actor=p.picture(nxt);next_receiver=p.picture(by_id['thrown-back-0'])
    continuation_pages=[]
    for color,label in [('#252b35','深底'),('#f1e9df','浅底')]:
        suffix='dark' if label=='深底' else 'light'
        for marked in [False,True]:
            prev=scene(prev_actor,prev_receiver,pair['whole_179_display_origin_in_actor_canvas'],color,marked,rpoint)
            next_=scene(next_actor,next_receiver,continuation['next_thrown_back0_full_cell_origin'],color,marked,rpoint)
            continuation_pages.append(continuation_page(prev,next_,OUT/f"phase05-to-thrown-back0-{suffix}{'-marked' if marked else ''}.jpg",color,label,marked,rpoint))
    after0=scene(next_actor,next_receiver,continuation['next_thrown_back0_full_cell_origin'],'#252b35')
    continuation_pages.append(scene_page(after0,OUT/'thrown-back0-complete-scene-2x-dark.jpg','raw44–47 / 哥莫拉源11＋本人现装倒立0 / 完整接续候选'))
    # 每raw帧可写自己的root_overrides，不要求所有phase用同一个root。
    hold=[]
    for pair in base['pairs'][:4]:
        hold.append({'raw_ticks':pair['raw_ticks'],'relative_facing_required':1,
            'actual_measured_actor_contact_local':pair['proposed_actor_grip'],
            'actual_receiver_hold_point_local':pair['proposed_receiver_hold_point'],
            'resulting_receiver_root_relative_actor':pair['proposed_receiver_root_relative_actor'],
            'keep_existing_shared_grip_G':True,
            'proposed_hold_root_override_expression':[f"{pair['proposed_actor_grip'][0]} - G.x",f"{pair['proposed_actor_grip'][1]} - G.y"],
            'explanation':'hold模式offset不是受方最终root；以真实受方A作hold_point，override=C_local−既有G，使最终受方root等于独立量得的C_local−A_local。未读取旧G数值，因此不伪造可直接安装的hold offset。'})
    roots=[{'raw_ticks':q['raw_ticks'],'proposed_root_overrides':{'ultraman':q['proposed_receiver_root_relative_actor']},'mode':'root','ground_required':False,'relative_facing_required':1} for q in base['pairs'][4:]]
    roots.append({'raw_ticks':[44,47],'proposed_root_overrides':{'ultraman':continuation['proposed_thrown_back0_root_relative_actor']},'mode':'root','ground_required':False,'relative_facing_required':1})
    dep={'status':'readonly_dependency_proposal_not_implemented','proposal':p.rec(BASE),
        'reason':'共享target.root无法同时保留旧受方默认值并表达初代本人04/05及倒立0独立根点；不能挪179源图、caster骨尺或切换hold模式绕过。',
        'smallest_generic_data_extension':'target.root_overrides：可选Dictionary，键为受方definition.id，值为整数[x,y]；缺身份项走既有target.root或[0,0]。每个target raw帧独立声明，不按角色写代码分支。',
        'root_mode_exact_proposals':roots,'hold_mode_independent_geometry_and_pending_materialization':hold,
        'generic_consumer_changes_needed':[
            '集中解析root offset；throw_resolver.sync和floor_safe_hold_sprite共同使用，保证hold楼面变体与最终坐标取同一offset。',
            'move_data.valid校验可选字典、非空字符串身份键与长度2整数坐标；不把错误值静默转0，保持现有无字段路径。',
            'release模式若以后使用覆盖，则offset需在release_goal_x/height按同一解析值消费；本任务没有改48以后释放或落地点。',
            'fighter_definition.fingerprint已有整份moves/state_frames，自然纳入新增数据；新增通用语义需按项目规则更新模拟版本指纹，不能冒称旧回放兼容。'],
        'later_validation_required':'缺省旧受方路径逐tick不变；身份覆盖/非法点/楼面变体/hold与root、双朝向、原输入独立回放、实际完整人物与44–71段接续。',
        'ground_actor_height_H_example':{'H':0,'phase05_root_height':89,'thrown_back0_root_height':99,'pelvis_R_height_both':182},
        'air_actor_height_H_example':'actor捕获后高度H时，phase05根高H+89、倒立0根高H+99、骨盆高同为H+182；真实main仍待。',
        'pelvis_continuity_is_not_full_pose_continuity_acceptance':True,'actor_next_source':nxt['image'],
        'actual_contact_or_continuation_accepted':False,'root_grip_or_runtime_accepted':False,
        'strict_size_accepted':False,'post_requests':0,'png_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0}
    p.save(OUT/'minimal-generic-root-override-dependency.json',dep)
    p.save(OUT/'complete-pages-index.json',{'base_pair_pages':[q['clean_pair_page'] for q in base['pairs']],
        'complete_2x_pair_pages':pages,'complete_continuation_pages':continuation_pages,
        'all_pages_are_full_scene_no_alpha_or_body_crops':True,'all_acceptance_pending_root':True})
    after={k:p.sha(p.ROOT/k) for k in before};assert before==after
    p.save(OUT/'readonly-byte-verification.json',{'before':before,'after':after,'unchanged':True,
        'old_frozen_directories_not_written':True,'png_writes':0,'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    print(json.dumps({'report':str(OUT),'root_override_proposals':roots,'hold_offsets_pending_existing_G_not_read':True},ensure_ascii=False))

if __name__=='__main__':main()
