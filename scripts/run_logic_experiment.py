"""Final fresh/resumable main experiment. No self-refinement or custom interpreters."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from api_compat import generate
from logic_final import (ROOT, UPSTREAM, DATASETS, FORMAT_FILE, atomic_json, digest,
                         prompt_files, build_prompt, cot_answer, validate_rows, check_runtime, format_constraint)


def load_environment():
    # Explicit exported values take precedence over the local untracked .env.
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


def config(dataset, split, rows, model):
    program, cot = prompt_files(dataset)
    return {'policy_version': 'final-1', 'dataset': dataset, 'split': split,
            'sample_ids': [row['id'] for row in rows], 'model': model, 'reference_model': 'gpt-4',
            'temperature': 0., 'top_p': 1., 'max_tokens': 1024, 'stop': '------',
            'api_style': 'chat', 'interpreter': 'author-code', 'self_refinement': False,
            'cot_postprocessing': 'ld-explicit-option-v1' if dataset == 'LogicalDeduction' else 'markdown-only-then-author-evaluator',
            'format_constraint': format_constraint(dataset),
            'author_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=UPSTREAM, text=True).strip(),
            'source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in
                (program, cot, FORMAT_FILE, *( [ROOT / f'configs/prompts/{dataset}-format-minimal.txt'] if dataset in ('LogicalDeduction','AR-LSAT') else []),
                 UPSTREAM / f'data/{dataset}/{split}.json',
                 ROOT / 'scripts/logic_final.py', ROOT / 'scripts/evaluate_logic_experiment.py',
                 *([ROOT / 'scripts/logical_deduction_compat.py', ROOT / 'scripts/logical_deduction_cot.py'] if dataset == 'LogicalDeduction' else []),
                 UPSTREAM / 'models/evaluation.py')},
            'endpoint_sha256': hashlib.sha256(os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').encode()).hexdigest()}


def record_path(run, stage, sample_id):
    return run / stage / 'records' / (hashlib.sha256(sample_id.encode()).hexdigest() + '.json')


def read_records(run, stage, expected):
    records = [json.loads(p.read_text()) for p in (run / stage / 'records').glob('*.json')]
    lookup = {row['id']: row for row in expected}
    ids = [record['row']['id'] for record in records]
    if len(ids) != len(set(ids)) or set(ids) - set(lookup):
        raise ValueError('Invalid saved records')
    for record in records:
        row = record['row']
        if record['log']['id'] != row['id'] or record['log']['prompt'] != build_prompt(record['dataset'], stage, lookup[row['id']]):
            raise ValueError('Saved prompt/ID mismatch')
    validate_rows([x['row'] for x in records], expected, complete=False)
    return records


def snapshots(run, stage, expected):
    records = read_records(run, stage, expected)
    order = {row['id']: i for i, row in enumerate(expected)}
    records.sort(key=lambda record: order[record['row']['id']])
    atomic_json(run / stage / ('programs.json' if stage == 'program' else 'cot.json'), [x['row'] for x in records])
    logpath = run / stage / 'api.jsonl'
    tmp = logpath.with_suffix('.tmp')
    with tmp.open('w') as stream:
        for record in records:
            stream.write(json.dumps(record['log'], ensure_ascii=False) + '\n')
    tmp.replace(logpath)
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=DATASETS, required=True)
    parser.add_argument('--split', choices=['dev', 'test'], default='dev')
    parser.add_argument('--model', default='gpt-5.6-sol')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--sample-ids', type=Path)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--prepare-only', action='store_true', help='Freeze config and IDs without API calls')
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 4:
        parser.error('--workers must be 1..4')
    if args.limit is not None and args.sample_ids:
        parser.error('Choose --limit or --sample-ids')
    load_environment()
    rows = json.loads((UPSTREAM / f'data/{args.dataset}/{args.split}.json').read_text())
    if args.sample_ids:
        ids = json.loads(args.sample_ids.read_text())
        lookup = {row['id']: row for row in rows}
        if not ids or len(ids) != len(set(ids)) or set(ids) - set(lookup):
            parser.error('Invalid sample IDs')
        rows = [lookup[x] for x in ids]
    if args.limit is not None:
        if not 1 <= args.limit <= len(rows):
            parser.error('Invalid --limit')
        rows = rows[:args.limit]
    cfg = config(args.dataset, args.split, rows, args.model)
    if args.resume:
        run = args.resume.resolve()
        if json.loads((run / 'run.json').read_text()) != cfg:
            raise SystemExit('Resume refused: source/model/selection/config changed')
    else:
        run = ROOT / 'results' / f'logic-final-{args.dataset}-{time.time_ns()}'
        run.mkdir(parents=True)
        atomic_json(run / 'run.json', cfg)
        for stage in ('program', 'cot'):
            (run / stage / 'records').mkdir(parents=True)
    print('RUN', run, flush=True)
    if args.prepare_only:
        return
    check_runtime(args.dataset)
    if not os.getenv('OPENAI_API_KEY'):
        raise SystemExit('Missing OPENAI_API_KEY')
    records = {stage: read_records(run, stage, rows) for stage in ('program', 'cot')}
    counts = {stage: len(value) for stage, value in records.items()}
    done = {stage: {record['row']['id'] for record in value} for stage, value in records.items()}
    jobs = iter((stage, row) for row in rows for stage in ('program', 'cot') if row['id'] not in done[stage])

    def task(stage, row):
        prompt = build_prompt(args.dataset, stage, row)
        started = time.time()
        raw, response, style, model = generate(prompt, 'gpt-4', args.model, 'chat', 1024, 0., '------', 120)
        answer_fields = cot_answer(raw)
        if stage == 'cot' and args.dataset == 'LogicalDeduction':
            from logical_deduction_cot import extract_ld_cot
            answer_fields = extract_ld_cot(raw, len(row['options']))
        result = ({**row, 'raw_logic_programs': [raw]} if stage == 'program' else
                  {'id': row['id'], 'question': row['question'], 'answer': row['answer'], **answer_fields})
        return {'dataset': args.dataset, 'stage': stage, 'row': result,
                'log': {'id': row['id'], 'prompt': prompt, 'response': response,
                        'api_style': style, 'api_model': model, 'seconds': time.time() - started}}

    failures = []
    with (run / 'execution.jsonl').open('a') as stream:
        stream.write(json.dumps({'time': time.time(), 'workers': args.workers, 'saved': counts}) + '\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {}
        def submit_one():
            job = next(jobs, None)
            if job:
                pending[pool.submit(task, *job)] = job
        for _ in range(args.workers):
            submit_one()
        while pending:
            ready, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in ready:
                stage, row = pending.pop(future)
                try:
                    record = future.result()
                    # One atomic record includes BOTH output and request; restart never loses one half.
                    atomic_json(record_path(run, stage, row['id']), record)
                    counts[stage] += 1
                    atomic_json(run / 'status.json', {'state': 'generating', 'n': len(rows), **counts})
                    print(counts, flush=True)
                except Exception as ex:
                    failures.append({'stage': stage, 'id': row['id'], 'error': type(ex).__name__ + ': ' + str(ex)})
                if not failures:
                    submit_one()
            # On failure, drain and save other in-flight successes; submit nothing new.
    for stage in ('program', 'cot'):
        snapshots(run, stage, rows)
    if failures:
        atomic_json(run / 'failures.json', failures)
        atomic_json(run / 'status.json', {'state': 'stopped_on_failure', 'n': len(rows), **counts})
        raise SystemExit('Saved checkpoint; see failures.json. No semantic retry performed.')
    subprocess.run([sys.executable, str(ROOT / 'scripts/evaluate_logic_experiment.py'), '--run', str(run)], cwd=ROOT, check=True)
    atomic_json(run / 'status.json', {'state': 'complete', 'n': len(rows), **counts})

if __name__ == '__main__':
    main()
