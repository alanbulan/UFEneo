"""哥莫拉独立台账和正式帧检查，不修改其他会话的覆盖表/扫描结果。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,collections,math,copy
from gomora_qa import *
from loop_qa import evaluate
import gomora_install as install

# 本轮独立输出，避免覆盖并行会话尚未提交的旧报告。
OUT=ROOT/'reports/review/2026-10-23/gomora-installed/verify'
if (ROOT/'content/fighters/gomora/installation-fourth-2026-10-23.json').exists():
 OUT=ROOT/'reports/review/2026-10-23/gomora-fourth-installed/verify'

def main():
 ledger=read(WORK/'ledger.json');rows=ledger['requests'];errors=[]
 assert ledger['limits']=={'per_asset':10}
 assert [r['ledger_sequence'] for r in rows]==list(range(1,len(rows)+1))
 counts=collections.Counter(r['action'] for r in rows)
 assert max(counts.values())<=10
 registry=read(WORK/'asset-registry.json')['assets'];frame_requests=collections.Counter()
 for row in rows:
  entry=registry.get(row['action'])
  if entry:
   for i in entry['indices']:frame_requests[(entry['action'],i)]+=1
 assert max(frame_requests.values(),default=0)<=10,'整条请求与补帧必须共计固定帧10次'
 for row in rows:
  assert row['fighter']=='gomora' and row['quality']=='high'
  if row.get('imported_from_shared_ledger'):continue
  assert row['action'] in read(WORK/'asset-registry.json')['assets']
  assert sha(ROOT/row['brief'])==row['brief_sha256']
  assert len(row['inputs'])==row['input_image_count']
  for p in row['inputs']:assert sha(ROOT/p['path'])==p['sha256']
  if row['result']=='submitted_remote_unknown':errors.append('仍有在途/远端未知请求：'+row['action'])
  output=ROOT/row['output']
  if row['result']=='alpha_rejected':output=output.parent/'rejected'/output.name
  if output.exists():
   metadata=read(output.with_suffix('.metadata.json'))
   assert metadata['requested_quality']=='high' and metadata['background_requested']=='transparent'
   assert sha(output)==metadata['image_sha256']
 result=[];mp=ROOT/'assets/fighters/gomora/animations/manifest.json'
 if mp.exists():
  for action,clip in read(mp)['clips'].items():
   fourth_path=ROOT/'content/fighters/gomora/installation-fourth-2026-10-23.json'
   fourth=read(fourth_path)['actions'] if fourth_path.exists() else {}
   if action in fourth:
    from gomora_fourth_install import audit_clip as audit_fourth
    record=fourth[action];states=read(ROOT/'content/fighters/gomora/state_frames.json')
    assert sha(ROOT/record['source'])==record['source_sha256']==clip['atlas_sha256']
    assert clip['motion_review']['commander_approved'] and clip['motion_review']['atlas_sha256']==clip['atlas_sha256']
    move_path=ROOT/f'content/fighters/gomora/moves/{action}.json'
    if move_path.exists():assert read(move_path)['frames']==states[action]
    assert audit_fourth(action,clip,states[action])==record['audit']
    result.append(dict(action=action,installed_approved=True,audit=record['audit']))
    continue
   installed_path=ROOT/'content/fighters/gomora/installation-2026-10-23.json'
   installed=read(installed_path)['actions'] if installed_path.exists() else {}
   if action in installed:
    from gomora_ready_install import audit_clip
    record=installed[action]
    assert sha(ROOT/record['source'])==record['source_sha256']==clip['atlas_sha256']
    assert clip['motion_review']['commander_approved'] and clip['motion_review']['atlas_sha256']==clip['atlas_sha256']
    states=read(ROOT/'content/fighters/gomora/state_frames.json')
    move_path=ROOT/f'content/fighters/gomora/moves/{action}.json'
    seq=read(move_path)['frames'] if move_path.exists() else states[action]
    assert seq==states[action]
    audit=audit_clip(action,clip,seq)
    assert audit==record['audit']
    result.append(dict(action=action,installed_approved=True,audit=audit))
    continue
   atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA');hq=read(ROOT/clip['head_qa']);images=[];actual_heads=[]
   assert sha(ROOT/clip['texture'].removeprefix('res://'))==clip['atlas_sha256']
   assert len(clip['rects'])==len(clip['ticks'])==len(hq['frames'])
   for i,(rect,record) in enumerate(zip(clip['rects'],hq['frames'])):
    x,y,w,h=rect;assert (w,h)==CELL and clip['anchors'][i]==list(ANCHOR)
    im=atlas.crop((x,y,x+w,y+h));source=(ROOT/clip['head_qa']).parent/record['image']
    assert sha(source)==record['image_sha256'] and sha(ROOT/record['source'])==record['source_sha256']
    assert im.tobytes()==Image.open(source).convert('RGBA').tobytes()
    # 最终图必须和量化后的GPT基线完全相同，不能后处理按区域压暗。
    baseline=source.with_name(source.name.replace('frame-','color-source-'))
    assert im.tobytes()==Image.open(baseline).convert('RGBA').tobytes()
    hint=record['measurement']['eye'] if record['measurement'] else None
    if record['measurement'] and record['measurement'].get('eye_detected') is False:
     assert record.get('raw_head'),'成品眼不可见时必须保留真实原图眼定位依据'
     assert np.linalg.norm(np.array(record['raw_head']['eye'])*record['scale']+record['offset']-hint)<1e-6
    # 旧模板只保留历史定位；头部核对用已校准的v2软门，循环眼高重新取实际黄眼像素。
    head=copy.deepcopy(record['measurement']) if record['measurement'] else None
    actual_eye=eye(im)
    if head and actual_eye:head['eye']=actual_eye['center']
    if clip['loop'] and not actual_eye:errors.append(f'{action}/{i}: 循环缺可见黄眼，不能拿原图提示代替')
    q=validate_frame(im,head,record['standing_required'],record['head_hidden'],record.get('standing_target',192));errors.extend(f'{action}/{i}: {s}' for s in q['issues'])
    images.append(im);actual_heads.append(head)
    result.append(dict(action=action,frame=i,head_v2=q['head_v2'],legacy_head_locator=head,standing=q['standing_height'],tail=record['tail'],issues=q['issues']))
   if clip['loop']:
    q=evaluate([h['eye'] for h in actual_heads],action);errors.extend(action+': '+s for s in q['issues'])
   if action.startswith('walk_'):
    walk=read(WORK/action/'walk-qa.json');sources=[(ROOT/clip['head_qa']).parent/r['image'] for r in hq['frames']]
    if not install.walk_manual_release(action,walk,sources):errors.extend(action+': '+s for s in walk['issues'])
    else:assert clip['rhythm_review']==read(WORK/action/'manual-release.json')
    assert clip['ticks']==walk['ticks']
   if action in install.ATTACKS:
    move=read(ROOT/f'content/fighters/gomora/moves/{action}.json')
    assert len(move['frames'])==sum(move[k] for k in ['startup','active','recovery'])==sum(clip['ticks'])
    assert any(r['events'] for r in move['frames'])
    assert all(not fr['hitboxes'] for fr in move['frames'][:move['startup']]+move['frames'][-move['recovery']:])
    assert all(fr['hitboxes'] for fr in move['frames'][move['startup']:move['startup']+move['active']])
  definition=read(ROOT/'content/fighters/gomora/definition.json');assert definition['pilot_playable']
  assert (definition['playable'] and definition.get('selection_authorization') and definition['pilot_manual_ready']) or (not definition['playable'] and not definition['pilot_manual_ready'])
  clips=read(mp)['clips'];states=read(ROOT/'content/fighters/gomora/state_frames.json')
  if all(p in clips for p in ['dash_start','dash','dash_stop']):
   expected=[];offset=0
   for key in ['dash_start','dash','dash_stop']:
    assert clips[key]['simulation_sprite_offset']==offset
    expected.extend(i+offset for i,t in enumerate(clips[key]['ticks']) for _ in range(t));offset+=len(clips[key]['rects'])
   assert len(expected)==22 and [r['sprite'] for r in states['dash']]==expected,'冲刺模拟必须包含完整九帧，不能只有跑步12tick'
 summary=dict(requests=len(rows),new_requests=sum(not r.get('imported_from_shared_ledger') for r in rows),categories=dict(collections.Counter(r.get('category','历史定稿') for r in rows)),retry_requests=sum(r.get('sequence',1)>1 for r in rows),failed_requests=sum(r['result'] in ['alpha_rejected','failed_or_remote_unknown','interrupted_remote_unknown','submitted_remote_unknown'] for r in rows),max_fixed_frame_requests=max(frame_requests.values(),default=0),frames=result,errors=errors)
 save(OUT/'gomora-verification.json',summary)
 if errors:print('\n'.join(errors));raise SystemExit(1)
 print('哥莫拉：独立账本、源图指纹、整帧尺寸/Alpha/孤岛/调色基线、循环和帧数据一致。尾长与角仍待人工审片。')

if __name__=='__main__':main()
