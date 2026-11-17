"""只生成最小通用throw_target_air补丁/前后哈希；不应用产品代码。"""
from pathlib import Path
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-throw-target-patch-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();rows=[];patch=[]
 files=['core/combat/hit_resolver.gd','core/combat/move_data.gd','core/combat/match_director.gd']
 for rel in files:
  src=ROOT/rel;before=src.read_bytes();text=before.decode('utf8').replace('\r\n','\n');after=text
  if rel.endswith('/hit_resolver.gd'):
   after=after.replace('const PUSHBACK_BOUNDARY_REVISION := 1\n','const PUSHBACK_BOUNDARY_REVISION := 1\nconst THROW_TARGET_RULE_REVISION := 1\n',1)
   old='\t\tvar air_throw: bool=attacker.move_id=="air_throw"\n\t\tif air_throw!=(target.height>0):return false\n\t\tif not UfeThrowResolver.can_capture(target,attacker.definition.moves[attacker.move_id]):return false'
   new='\t\tvar throw_move: Dictionary=attacker.definition.moves[attacker.move_id]\n\t\tvar air_throw: bool=bool(throw_move.get("throw_target_air",attacker.move_id=="air_throw"))\n\t\tif air_throw!=(target.height>0):return false\n\t\tif not UfeThrowResolver.can_capture(target,throw_move):return false'
   assert after.count(old)==1;after=after.replace(old,new,1)
  elif rel.endswith('/move_data.gd'):
   old='\tif move.has("air_only"):\n'
   new='\tif move.has("throw_target_air"):\n\t\tif not move.throw_target_air is bool or str(move.get("kind",""))!="throw":return false\n\tif move.has("air_only"):\n'
   assert after.count(old)==1;after=after.replace(old,new,1)
  else:
   old='["hit_pushback_bounds", UfeHitResolver.PUSHBACK_BOUNDARY_REVISION]]'
   new='["hit_pushback_bounds", UfeHitResolver.PUSHBACK_BOUNDARY_REVISION], ["throw_target_air", UfeHitResolver.THROW_TARGET_RULE_REVISION]]'
   assert after.count(old)==1;after=after.replace(old,new,1)
  assert after!=text
  newline='\r\n' if b'\r\n' in before else '\n';proposed=after.replace('\n',newline).encode('utf8')
  target=OUT/'proposed'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(proposed)
  patch.extend(difflib.unified_diff(text.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
  rows.append(dict(path=rel,before_sha256=sha(before),proposed_sha256=sha(proposed),proposed=target.relative_to(ROOT).as_posix(),
   original_line_endings='CRLF' if newline=='\r\n' else 'LF'))
  assert src.read_bytes()==before
 (OUT/'throw-target-air.patch').write_text(''.join(patch),'utf8',newline='\n')
 contract=dict(files=rows,applied=False,godot_run=False,code_tests_run=False,
  field=dict(name='throw_target_air',type='bool',valid_only_for_kind='throw',
   missing_default='move_id == air_throw；保持现有地投/空投规则',true='只允许target.height>0',false='只允许target.height<=0'),
  unchanged=['实体hit/hurt相交','can_capture状态/拆投规则','throw begin/sync/release','移动/费用/伤害','原旧缺省招式行为'],
  fingerprint=dict(new_explicit_component=['throw_target_air',1],old_fingerprint_expected_rejected=True),
  root_required_tests=['旧缺省地投/空投真实输入逐tick不变','显式true/false实际捕获门','错误类型0/1/字符串/null和非throw验证拒绝',
   '新旧内容指纹回放拒绝与新同指纹回放一致','新招真实默认站位与自然跳入实体上背，不预设height/x/vy/thrown',
   '前三实际tick拆投，空抓/远跳/高跳/站蹲双防/墙边/受方完整路径'],
  limitation='这是未应用代码合同；静态差异不等于Godot解析/逻辑/回放通过，不能据此安装捕获框或宣告三级完成。')
 with (OUT/'patch-contract.json').open('x',encoding='utf8') as f:json.dump(contract,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(report=str(OUT),product_changed=False),ensure_ascii=False))
if __name__=='__main__':main()
