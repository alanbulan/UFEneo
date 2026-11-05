"""外编排失败关闭测试：模拟旧runner通过但外门拒绝，不能写成功总回执。"""
import json
from pathlib import Path
import run_strict as runner
R=runner.gate.R
calls=[]
def fake_run(contract,out,headless):
 calls.append('runner');out.mkdir();(out/'runner-result.json').write_text('{"completed":true}')
def reject(out):calls.append('gate');raise AssertionError('injected_external_gate_failure')
runner.bundle.run=fake_run;runner.gate.check=reject
out=R/'orchestration-negative-v1';assert not out.exists()
try:runner.run(out,True)
except AssertionError as e:assert str(e)=='injected_external_gate_failure'
else:raise AssertionError('external rejection was swallowed')
assert calls==['runner','gate'] and not (out/'strict-final-result.json').exists()
result={'passed':True,'calls':calls,'external_rejection_propagated':True,'success_receipt_absent':True,'godot_started':False,'scope':'mock orchestration only; not graphical execution','orchestrator_sha256':runner.sha(Path(runner.__file__))}
p=R/'orchestration-negative-v1.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(p,runner.sha(p))
