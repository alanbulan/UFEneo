"""唯一最终验收编排：旧v3运行后强制外部严格事件门，失败不能签总回执。"""
import argparse,hashlib,json
from pathlib import Path
import main_bundle as bundle
import test_check as gate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(out,headless=False):
 contract=gate.R/'contract-v3.json';checker=Path(gate.__file__);self=Path(__file__)
 pinned={'contract':sha(contract),'checker':sha(checker),'orchestrator':sha(self)}
 assert not out.exists()
 bundle.run(contract,out,headless)
 # Mandatory, not a README-only optional step. No success receipt is emitted before this returns.
 result=gate.check(out)
 assert pinned=={'contract':sha(contract),'checker':sha(checker),'orchestrator':sha(self)}
 result.update(schema='ufeneo.luna.strict-external-run.v1',source_sha256=pinned,runner_result_sha256=sha(out/'runner-result.json'),headless=headless,v3_inner_gate_repaired=False)
 receipt=out/'strict-final-result.json';assert not receipt.exists();receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(receipt,sha(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--headless',action='store_true');a=p.parse_args();run(a.out.resolve(),a.headless)
