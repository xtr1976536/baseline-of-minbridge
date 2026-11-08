"""Exercise all frozen rows/eight runner cells and resume, without an LLM.

This checks orchestration, journals and denominators only. It deliberately uses
an always-abstaining protocol stub, writes only under tmp/, and is NOT a model
evaluation or an accuracy result. Actual GBFR reasoning is tested by pytest.
"""
import asyncio
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gbfr import runner
from gbfr.data import jsonl, sha256, write_json
from gbfr.types import Prediction


async def main():
    config=runner.resolve_paths(ROOT/'configs/main.json')
    graph,datasets=runner.preflight(config)
    scratch=ROOT/'tmp'
    scratch.mkdir(exist_ok=True)
    output=Path(tempfile.mkdtemp(prefix='offline-matrix-',dir=scratch)).resolve()
    assert output.is_relative_to(scratch.resolve())
    config['output_dir']=str(output)
    calls=[]
    class Client:
        def __init__(self,*args):
            self.records=[]
        async def close(self):
            pass
    class Stub:
        def __init__(self,*args):
            pass
        async def predict(self,question,context):
            calls.append((question,context))
            return Prediction('abstained',None,{},None,{'offline_protocol_stub':True},'Offline runner validation only')
    originals=(runner.ChatClient,runner.GBFR)
    runner.ChatClient,runner.GBFR=Client,Stub
    cells=[]
    try:
        with (output/'progress.log').open('w',encoding='utf-8') as log, redirect_stdout(log):
            for backbone in config['backbones']:
                for name,samples in datasets.items():
                    r=await runner.run_cell(config,graph,name,samples,backbone)
                    path=output/backbone/name/'predictions.jsonl'
                    digest=sha256(path)
                    before=len(calls)
                    await runner.run_cell(config,graph,name,samples,backbone)
                    assert sha256(path)==digest and len(calls)==before
                    assert len(jsonl(path))==len(samples) and r['n']==len(samples) and r['errors']==0
                    cells.append({'backbone':backbone,'dataset':name,'rows':len(samples),'journal_sha256':digest,'resume_without_recompute':True})
    finally:
        runner.ChatClient,runner.GBFR=originals
    report={'purpose':'Offline orchestration/journal/denominator validation only; NOT GBFR accuracy',
            'real_api_calls':0,'output_dir':str(output),'cells':cells,'total_rows':len(calls),
            'all_frozen_rows_exercised':len(calls)==sum(map(len,datasets.values()))*2,
            'all_resume_checks_passed':True}
    write_json(ROOT/'research/reconstruction/offline_matrix.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    asyncio.run(main())
