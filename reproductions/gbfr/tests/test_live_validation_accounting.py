"""Partial live runs must not manufacture rejection measurements."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('live_validation',Path(__file__).parents[1]/'scripts/run_live_repair_validation.py')
live=importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)

def examples():
    return [{'id':'a','question':'How many?', 'answer':'2','context':'','unanswerable':False},
            {'id':'b','question':'How many?', 'answer':None,'context':'','unanswerable':True}]

def test_no_processed_counterfactual_is_unmeasured():
    m=live.measured_metrics(examples(),[{'sample_id':'a','status':'answered','value':2}],2,'fixed')
    assert m['processed_metrics']['total_accuracy']==100
    assert m['processed_metrics']['abstention_accuracy'] is None
    assert m['missing']==1 and live.percentage(None)=='未测'

def test_technical_error_never_counts_as_rejection():
    m=live.measured_metrics(examples(),[{'sample_id':'b','status':'error'}],2,'fixed')
    assert m['processed_metrics']['n']==1
    assert m['processed_metrics']['errors']==1
    assert m['processed_metrics']['abstention_accuracy']==0
    assert not m['complete']

def test_fixed_scope_has_forty_unique_native_inputs():
    manifest,selected=live.load_selection()
    assert manifest['total']==40
    assert sum(len(ss) for ss in selected.values())==40
    assert len({s['id'] for ss in selected.values() for s in ss})==40
