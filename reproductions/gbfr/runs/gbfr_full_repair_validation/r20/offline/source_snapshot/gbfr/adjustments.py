"""Freeze fair, prediction-independent adjustments authorized for the main run."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

from .data import EXPECTED, FILES, jsonl, sha256, write_json
from .metrics import parse_number
from .reconciliation import FINQA_2022, compatible_rows, negative_lineage
from .types import AssetError, dumps

POLICY = 'paper-method-v1'


def eligible(name, answer):
    return (name == 'FinanceReasoning' and isinstance(answer, bool)) or parse_number(answer) is not None


def correct_cf_gold(sample):
    """Two deterministic arithmetic corrections, made before any prediction."""
    src = sample['source']
    if src['file'] != '金融指标计算.json' or src['index'] not in {18, 66}:
        return None
    if src['index'] == 18:
        old = '-0.037'
        value = Decimal('-214.8') * 10000 / (Decimal('5.799') * 100000000)
        new = str(value.quantize(Decimal('.0001'), rounding=ROUND_HALF_UP))
        evidence, reason = ['-214.8', '5.799'], 'ROS = net income / sales; 万 and 亿 converted to the same currency scale'
    else:
        old = '4.26%'
        value = (1 - Decimal('6.4515')/Decimal('6.7261')) * 100
        new = str(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) + '%'
        evidence, reason = ['6.4515', '6.7261'], 'CNY depreciation measured in USD per CNY, not USD appreciation in the inverse quote'
    if sample['answer'] != old or not all(token in sample['context'] for token in evidence):
        raise AssetError('CF correction precondition changed; review required')
    sample['answer'] = new
    return {'sample_id': sample['id'], 'source': src, 'old_answer': old, 'new_answer': new,
            'reason': reason, 'context_sha256': __import__('hashlib').sha256(sample['context'].encode()).hexdigest()}


def prepare_main(root: Path, source_dir: Path, output: Path, audit_dir: Path):
    """Graph building is separate: this function's gold inputs never reach it."""
    upstream = root / 'research/upstream'
    parents, negative_sources = {}, {}
    for name, (files, negative_file) in FILES.items():
        if name in {'FinQA', 'TAT-QA'}:
            path = (root / 'data/raw/official/history' / (FINQA_2022['commit']+'.json') if name == 'FinQA'
                    else root / 'data/raw/official/TAT-QA.json')
            parents[name] = compatible_rows(name, json.loads(path.read_text(encoding='utf-8')))
        else:
            parents[name] = []
            for file in files:
                parents[name].extend(json.loads((upstream / 'data' / name / file).read_text(encoding='utf-8')))
        negative_sources[name] = json.loads((upstream / 'data' / name / negative_file).read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'schema_version': 1, 'policy': POLICY, 'predictions_used': False,
        'graph_builder_reads_test_data': False,
        'source_manifest_sha256': sha256(source_dir / 'manifest.json'),
        'datasets': {}, 'gold_corrections': [],
        'selection_rule': 'Keep scalar numerical targets; keep native FinanceReasoning boolean comparisons; apply the same target eligibility to original and counterfactual lineage. Never pick a component of a vector answer.'}
    for name in EXPECTED:
        path = source_dir / (name+'.jsonl')
        rows = jsonl(path)
        lineage = negative_lineage(parents[name], negative_sources[name])
        if lineage['ambiguous_or_missing']:
            raise AssetError('Cannot freeze counterfactual target eligibility: ' + name)
        links = {link['negative_index']: link['source_candidates'][0] for link in lineage['links']}
        kept, exclusions, corrections = [], [], []
        for sample in rows:
            if sample['unanswerable']:
                parent = parents[name][links[sample['source']['index']]]
                answer = parent.get('ground_truth') if name == 'FinanceReasoning' else parent.get('answer')
                if not eligible(name, answer):
                    exclusions.append({'sample_id': sample['id'], 'source': sample['source'],
                        'reason': 'counterfactual_of_non_scalar_or_unverifiable_original_target',
                        'original_answer': answer, 'parent_index': links[sample['source']['index']]})
                    continue
            elif not eligible(name, sample['answer']):
                exclusions.append({'sample_id': sample['id'], 'source': sample['source'],
                    'reason': 'non_scalar_numeric_answer', 'original_answer': sample['answer']})
                continue
            if name == 'CFBenchmark' and not sample['unanswerable']:
                correction = correct_cf_gold(sample)
                if correction:
                    corrections.append(correction)
            kept.append(sample)
        destination = output / (name+'.jsonl')
        destination.write_text(''.join(dumps(s)+'\n' for s in kept), encoding='utf-8')
        counts = {'original': sum(not s['unanswerable'] for s in kept),
                  'counterfactual': sum(s['unanswerable'] for s in kept), 'total': len(kept)}
        baseline = source_dir / (name+'.exclusions.json')
        baseline_exclusions = json.loads(baseline.read_text(encoding='utf-8')) if baseline.exists() else []
        write_json(output / (name+'.adjustments.json'), {'policy': POLICY, 'exclusions': exclusions,
                   'upstream_preparation_exclusions': baseline_exclusions, 'gold_corrections': corrections})
        manifest['datasets'][name] = {'actual': counts, 'expected_frozen': counts,
            'expected_table4': EXPECTED[name], 'counts_match_paper': counts == EXPECTED[name],
            'processed_sha256': sha256(destination), 'source_processed_sha256': sha256(path),
            'source_stage_counts': {'original': sum(not s['unanswerable'] for s in rows),
                                    'counterfactual': sum(s['unanswerable'] for s in rows), 'total': len(rows)},
            'additional_exclusions': len(exclusions), 'exclusion_reasons': dict(Counter(e['reason'] for e in exclusions)),
            'adjustments_sha256': sha256(output / (name+'.adjustments.json')),
            'corrections': corrections, 'unresolved_gold_disagreements': [],
            'retained_ids': [s['id'] for s in kept]}
        manifest['gold_corrections'].extend(corrections)
    write_json(output / 'manifest.json', manifest)
    write_json(audit_dir / 'dataset_adjustments.json', manifest)
    return manifest
