import importlib.util
import json
import os
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('full_r19_controller',Path(__file__).resolve().parents[1]/'scripts/run_full_r19.py')
controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)


def record(ident,value=3):
    return {'sample_id':ident,'status':'answered','value':value,'meta':{},'trace':{'events':['large source trace']}}


def line(p):return json.dumps(p).encode()+b'\n'


def shard(path,ids):return {'dataset':'FinQA','ids':set(ids),'journal':path}


def test_incremental_progress_waits_for_a_complete_line_and_does_not_reread(tmp_path):
    p=tmp_path/'predictions.jsonl';one=line(record('f1'));two=line(record('f2'))
    p.write_bytes(one+two[:-3]);s=shard(p,['f1','f2']);reader=controller.JournalIndex()
    reader.poll([s]);assert set(reader.rows['FinQA'])=={'f1'}
    assert 'trace' not in reader.rows['FinQA']['f1']
    reader.poll([s]);assert len(reader.rows['FinQA'])==1
    with p.open('ab') as f:f.write(two[-3:])
    reader.poll([s]);assert set(reader.rows['FinQA'])=={'f1','f2'}


def test_progress_rejects_a_duplicate_instead_of_inflating_completion(tmp_path):
    p=tmp_path/'predictions.jsonl';p.write_bytes(line(record('f1'))+line(record('f1')))
    with pytest.raises(RuntimeError,match='duplicate'):controller.JournalIndex().poll([shard(p,['f1'])])


def test_progress_rejects_an_unrelated_sample(tmp_path):
    p=tmp_path/'predictions.jsonl';p.write_bytes(line(record('other-dataset')))
    with pytest.raises(RuntimeError,match='Unrelated'):controller.JournalIndex().poll([shard(p,['f1'])])


def test_merge_preserves_original_records_and_native_sample_order(tmp_path):
    a=tmp_path/'a.jsonl';b=tmp_path/'b.jsonl';a.write_bytes(line(record('f2'))+line(record('f1')));b.write_bytes(line(record('f3')))
    out=tmp_path/'merged.jsonl'
    controller.merge_journals([shard(a,['f1','f2']),shard(b,['f3'])],'FinQA',[{'id':i} for i in ['f1','f2','f3','unprocessed']],out)
    pp=[json.loads(s) for s in out.read_bytes().splitlines()]
    assert [p['sample_id'] for p in pp]==['f1','f2','f3']
    assert all(p['trace']==record('ignored')['trace'] for p in pp)


def test_invalid_merge_does_not_overwrite_an_existing_result(tmp_path):
    a=tmp_path/'a.jsonl';a.write_bytes(line(record('f1'))+line(record('f1')));out=tmp_path/'merged.jsonl';out.write_bytes(b'preserve me')
    with pytest.raises(RuntimeError,match='duplicate'):controller.merge_journals([shard(a,['f1'])],'FinQA',[{'id':'f1'}],out)
    assert out.read_bytes()==b'preserve me'


def test_exclusive_run_lock_prevents_a_second_paid_worker(tmp_path,monkeypatch):
    monkeypatch.setattr(controller,'OUT',tmp_path)
    assert controller.pid_alive(os.getpid()) is True
    controller.acquire_lock();before=(tmp_path/'run.lock').read_bytes()
    with pytest.raises(RuntimeError,match='live worker'):controller.acquire_lock()
    assert (tmp_path/'run.lock').read_bytes()==before
