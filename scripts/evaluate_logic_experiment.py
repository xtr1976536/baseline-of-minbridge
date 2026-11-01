"""Author solvers only. Markdown-only CoT cleanup is mandatory; raw scores retained."""
import argparse
import collections
import json
import os
import shutil
import sys
from pathlib import Path
from logic_final import (ROOT, UPSTREAM, PAPER, DATASETS, atomic_json, strip_markdown,
                         raw_cot_answer, validate_rows, build_prompt)


def reset_pyke():
    shutil.rmtree(UPSTREAM / 'models/compiled_krb', ignore_errors=True)
    for name in list(sys.modules):
        if name == 'compiled_krb' or name.startswith('compiled_krb.'):
            sys.modules.pop(name, None)


def load_author_solver(dataset):
    sys.path.insert(0, str(UPSTREAM / 'models'))
    if dataset in ('ProntoQA', 'ProofWriter'):
        from symbolic_solvers.pyke_solver.pyke_solver import Pyke_Program
        return Pyke_Program
    if dataset == 'FOLIO':
        from symbolic_solvers.fol_solver.prover9_solver import FOL_Prover9_Program
        return FOL_Prover9_Program
    if dataset == 'LogicalDeduction':
        from symbolic_solvers.csp_solver.csp_solver import CSP_Program
        return CSP_Program
    from symbolic_solvers.z3_solver.sat_problem_solver import LSAT_Z3_Program
    return LSAT_Z3_Program


def evaluate(dataset, programs, cot, expected):
    validate_rows(programs, expected)
    validate_rows(cot, expected)
    lookup = {row['id']: row for row in cot}
    solver = load_author_solver(dataset)
    from evaluation import evaluate_QA
    results = []
    for ex in programs:
        raw_backup = raw_cot_answer(lookup[ex['id']])
        backup = strip_markdown(raw_backup)
        status, error, prediction = 'success', '', None
        if dataset in ('ProntoQA', 'ProofWriter'):
            reset_pyke()
        try:
            program = solver(ex['raw_logic_programs'][0].strip(), dataset)
            if not program.flag:
                status = 'parsing error'
            else:
                answer, message = program.execute_program()
                if answer is None:
                    status, error = 'execution error', str(message)
                else:
                    prediction = program.answer_mapping(answer)
                    if prediction is None:
                        status, error = 'mapping error', 'Author mapper returned no option'
        except Exception as err:
            status, error = 'runtime exception', type(err).__name__ + ': ' + str(err)
        if status != 'success':
            prediction = backup
        results.append({'id': ex['id'], 'answer': ex['answer'], 'flag': status,
                        'predicted_answer': prediction,
                        'raw_predicted_answer': raw_backup if status != 'success' else prediction,
                        'error_message': error, 'fallback_source': 'CoT' if status != 'success' else None})
    if dataset in ('ProntoQA', 'ProofWriter'):
        reset_pyke()
    executable = [row for row in results if row['flag'] == 'success']
    raw_results = [dict(row, predicted_answer=row['raw_predicted_answer']) for row in results]
    cot_normalized = [dict(row, predicted_answer=strip_markdown(raw_cot_answer(row))) for row in cot]
    cot_raw = [dict(row, predicted_answer=raw_cot_answer(row)) for row in cot]
    n = len(results)
    summary = {'dataset': dataset, 'n': n, 'interpreter': 'author-code', 'self_refinement': False,
               'answer_processing': 'mandatory Markdown-only cleanup for CoT; author evaluate_QA unchanged',
               'accuracy': evaluate_QA(results), 'correct': round(evaluate_QA(results) * n),
               'raw_author_accuracy_without_cleanup': evaluate_QA(raw_results),
               'executable_rate': len(executable) / n,
               'executable_accuracy': evaluate_QA(executable) if executable else None,
               'executable': len(executable), 'fallback_count': n - len(executable),
               'cot_accuracy': evaluate_QA(cot_normalized), 'cot_correct': round(evaluate_QA(cot_normalized) * n),
               'cot_raw_author_accuracy_without_cleanup': evaluate_QA(cot_raw),
               'status_counts': dict(collections.Counter(row['flag'] for row in results)),
               'paper_gpt4_reference': PAPER[dataset],
               'differences': ['substitute model', '26-word format prefix; original examples unchanged',
                               'mandatory Markdown cleanup; raw metrics preserved',
                               'mapping/runtime failures explicitly recorded and backed up; not hidden'],
               'errors': [row for row in results if not evaluate_QA([row])]}
    summary['breakdown'] = {}
    for label in sorted({row['answer'] for row in results}):
        subset = [row for row in results if row['answer'] == label]
        summary['breakdown'][label] = {'n': len(subset), 'accuracy': evaluate_QA(subset)}
    if dataset == 'ProofWriter':
        for family in ('Att', 'Rel'):
            subset = [row for row in results if '_' + family in row['id']]
            if subset:
                summary['breakdown'][family] = {'n': len(subset), 'accuracy': evaluate_QA(subset)}
    return results, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, help='Final runner directory; verifies all stored request logs')
    parser.add_argument('--dataset', choices=DATASETS)
    parser.add_argument('--split', choices=['dev', 'test'], default='dev')
    parser.add_argument('--programs', type=Path)
    parser.add_argument('--cot', type=Path)
    parser.add_argument('--sample-ids', type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    cfg = None
    if args.run:
        if any((args.dataset, args.programs, args.cot, args.output_dir, args.sample_ids)):
            parser.error('--run cannot be combined with external artifact inputs')
        run = args.run.resolve()
        cfg = json.loads((run / 'run.json').read_text())
        args.dataset, args.split = cfg['dataset'], cfg['split']
        args.programs, args.cot = run / 'program/programs.json', run / 'cot/cot.json'
        output = run
        ids = cfg['sample_ids']
    else:
        if not all((args.dataset, args.programs, args.cot, args.output_dir)):
            parser.error('Supply --run or --dataset --programs --cot --output-dir')
        args.programs, args.cot = args.programs.resolve(), args.cot.resolve()
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        ids = json.loads(args.sample_ids.read_text()) if args.sample_ids else None
    data = json.loads((UPSTREAM / f'data/{args.dataset}/{args.split}.json').read_text())
    if ids is not None:
        lookup = {row['id']: row for row in data}
        if not ids or len(ids) != len(set(ids)) or set(ids) - set(lookup):
            parser.error('Invalid selection')
        data = [lookup[sample_id] for sample_id in ids]
    programs, cot = json.loads(args.programs.read_text()), json.loads(args.cot.read_text())
    validate_rows(programs, data)
    validate_rows(cot, data)
    verified = {}
    warnings = []
    if cfg:
        for stage, rows in [('program', programs), ('cot', cot)]:
            logs = [json.loads(line) for line in (output / stage / 'api.jsonl').read_text().splitlines()]
            byid = {log['id']: log for log in logs}
            if len(logs) != len(rows) or set(byid) != {row['id'] for row in rows}:
                raise ValueError('Incomplete request logs')
            source = {row['id']: row for row in data}
            for row in rows:
                log = byid[row['id']]
                expected_prompt = build_prompt(args.dataset, stage, source[row['id']])
                request = log['response']['_minbridge_request']
                if log['prompt'] != expected_prompt or request['messages'] != [{'role': 'user', 'content': expected_prompt}]:
                    raise ValueError('Prompt mismatch')
                for key in ('model', 'temperature', 'top_p', 'max_tokens', 'stop'):
                    if request[key] != cfg[key]:
                        raise ValueError('Request setting mismatch: ' + key)
                raw = log['response']['choices'][0]['message']['content'].strip()
                if raw != (row['raw_logic_programs'][0] if stage == 'program' else row['raw_output']):
                    raise ValueError('Output not aligned with response')
                if log['response'].get('_minbridge_audit_warnings'):
                    warnings.append({'stage': stage, 'id': row['id'], 'warnings': log['response']['_minbridge_audit_warnings']})
            verified[stage] = len(logs)
    original = Path.cwd()
    os.environ['PATH'] = str(ROOT / '.venv/bin') + os.pathsep + os.environ.get('PATH', '')
    prover_env = ROOT / '.local/prover9.env'
    if prover_env.exists():
        os.environ['PROVER9_BIN'] = prover_env.read_text().strip().split('=', 1)[1]
    os.chdir(UPSTREAM)
    try:
        results, summary = evaluate(args.dataset, programs, cot, data)
    finally:
        os.chdir(original)
    summary.update(requests_verified=verified, provider_usage_warnings=warnings,
                   source_programs=str(args.programs), source_cot=str(args.cot),
                   evaluation_scope='full_author_dataset' if len(data) == len(json.loads((UPSTREAM / f'data/{args.dataset}/{args.split}.json').read_text())) else 'explicit_subset',
                   source_note='fresh final run' if cfg else 'offline replay of existing outputs; no new API calls')
    atomic_json(output / 'predictions.json', results)
    atomic_json(output / 'summary.json', summary)
    paper = summary['paper_gpt4_reference']
    lines = ['# Logic-LM 最终配置评估', '', f'数据集：{args.dataset}；样本：{len(data)}；解释器：作者原版；无 self-refinement。', '',
             '| 指标 | 本次 | 论文 GPT-4 |', '|---|---:|---:|']
    for key, title in [('accuracy', '总体准确率'), ('executable_rate', '可执行率'), ('executable_accuracy', '可执行样本准确率'), ('cot_accuracy', '独立 CoT（先去 Markdown）')]:
        value = summary[key]
        lines.append(f'| {title} | ' + ('未定义' if value is None else f'{value:.2%}') + f' | {paper[key]:.2%} |')
    lines += ['', f'CoT 未去 Markdown 的作者原评分：{summary["cot_raw_author_accuracy_without_cleanup"]:.2%}。',
              f'回退样本：{summary["fallback_count"]}。清理仅移除显示标记，不根据答案或推理内容猜选项。',
              '', '保留作者提示词正文/示例和求解器，仅添加固定格式约束并做 Markdown 答案清理；不是底座以外零差异的严格复现。']
    (output / 'report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({key: summary[key] for key in ('dataset', 'n', 'accuracy', 'executable_rate', 'executable_accuracy', 'cot_accuracy', 'fallback_count')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
