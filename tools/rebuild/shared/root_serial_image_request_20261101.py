"""根串行已审合同：仅调用项目generate_image；离线预检、先占额、不自动重发。"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/"tools"),str(ROOT/"tools/rebuild/ultraman-omega")]
from codex_super_cinematic_art import official,read,ref,save,UNKNOWN
from art.image_budget import OfficialImageBudget


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief")
    parser.add_argument("--purpose",required=True)
    args=parser.parse_args()
    path=Path(args.brief).resolve()
    assert path.is_relative_to(ROOT) and path.name=="brief.json"
    folder=path.parent
    assert not (folder/"before-submit.json").exists(), "该合同已尝试，必须恢复原单，禁止重发。"
    brief=read(path)
    client,config,ledger=official()
    entries=read(ledger)["entries"]
    old=next(e for e in entries if e["id"]==UNKNOWN)
    assert Decimal(old["committed_usd"])==10
    assert not any(e["id"]!=UNKNOWN and any(t in str(e.get("status","")).lower() for t in ["unknown","reserved"]) for e in entries), "先恢复新未决请求。"
    refs=[ROOT/item["path"] for item in brief["references"]]
    assert all(ref(p)==item for p,item in zip(refs,brief["references"]))
    fields=client.image_fields(brief,None)
    OfficialImageBudget(config,"https://api.openai.com/v1",fields,refs)
    committed=sum(Decimal(e["committed_usd"]) for e in entries)
    assert committed+Decimal(str(config["official_budget"]["reserve_usd"]))<=60
    save(folder/"before-submit.json",dict(brief=ref(path),old_unknown_entry=old,
         committed_before_usd=str(committed),reserve_usd=str(config["official_budget"]["reserve_usd"]),
         fields_sha256=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest(),
         no_auto_retry=True,route="tools/art/pipeline.py(generate_image), https://api.openai.com/v1"))
    error=None
    try:
        client.generate_image(SimpleNamespace(model=None,reference=refs,out=folder/"candidate.png",mask=None,
             pose_guide=None,dry_run=False),brief,args.purpose)
    except Exception as exc:
        error=type(exc).__name__
    metadata=next((p for p in [folder/"candidate.metadata.json",folder/"rejected/candidate.metadata.json"] if p.is_file()),None)
    result=dict(error_type=error,image_returned=metadata is not None,no_retry=True)
    if metadata:result.update(metadata=ref(metadata),official_billing=read(metadata).get("official_billing"))
    save(folder/"submission-result.json",result)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if not metadata:raise SystemExit(1)


if __name__=="__main__":main()
