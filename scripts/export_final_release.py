"""Package explicitly selected final artifacts; no API calls and no credentials."""
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from logic_final import ROOT, UPSTREAM

SOURCES = {
    'ProofWriter': 'proofwriter-full-1793542998249517000',
    'ProntoQA': 'logic-final-ProntoQA-1793594917189717000',
    'FOLIO': 'logic-final-FOLIO-1793594917189562000',
    'LogicalDeduction': 'logic-final-LogicalDeduction-1793606303378768000',
    'AR-LSAT': 'logic-final-AR-LSAT-1793594917189562000',
}
DEST = ROOT / 'experiments/final'


def scrub(text):
    # Keep prompts and answers intact. Local machine paths alone are anonymized.
    return text.replace(str(ROOT), '<WORKSPACE>').replace('/Users/xiao/', '<USER_HOME>/')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = scrub(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
    if path.suffix == '.gz':
        path.write_bytes(gzip.compress(text.encode(), mtime=0))
    else:
        path.write_text(text)


def load(path):
    return json.loads(path.read_text())


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    index = {'release': '2026-11-02', 'author_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=UPSTREAM, text=True).strip(),
        'semantics': 'recorded = frozen historical score; current-policy = offline replay with latest code. Paired and standalone CoT are distinct runs.', 'datasets': {}}
    for dataset, name in SOURCES.items():
        source = ROOT / 'results' / name
        target = DEST / dataset
        for stage, filename in [('program', 'programs.json'), ('cot', 'cot.json')]:
            save(target / (filename + '.gz'), (source / stage / filename).read_text())
            save(target / (stage + '-api.jsonl.gz'), (source / stage / 'api.jsonl').read_text())
        if dataset == 'ProofWriter':
            recorded = load(ROOT / 'results' / f'logic-lm-ProofWriter-{name}-author-code-summary.json')
            predictions = ROOT / 'results' / f'logic-lm-ProofWriter-{name}-author-code.json'
        else:
            recorded, predictions = load(source / 'summary.json'), source / 'predictions.json'
        save(target / 'recorded-summary.json', recorded)
        save(target / 'recorded-predictions.json.gz', predictions.read_text())
        current = ROOT / 'results' / ('release-current-' + dataset)
        current_summary = load(current / 'summary.json')
        save(target / 'current-policy-summary.json', current_summary)
        save(target / 'current-policy-predictions.json.gz', (current / 'predictions.json').read_text())
        if dataset == 'LogicalDeduction':
            primary = current_summary
            primary['release_basis'] = 'latest CoT extraction applied offline to original paired answers; no program regeneration'
            save(target / 'predictions.json.gz', (current / 'predictions.json').read_text())
        else:
            primary = dict(recorded)
            primary['correct'] = round(primary['accuracy'] * primary['n'])
            primary['executable'] = round(primary['executable_rate'] * primary['n'])
            primary['fallback_count'] = primary['n'] - primary['executable']
            primary['cot_accuracy'] = current_summary['cot_accuracy']
            primary['cot_correct'] = current_summary['cot_correct']
            primary['paper_gpt4_reference'] = current_summary['paper_gpt4_reference']
            primary['release_basis'] = 'completed recorded main run; other datasets unchanged'
            save(target / 'predictions.json.gz', predictions.read_text())
        save(target / 'summary.json', primary)
        save(target / 'report.md', '# '+dataset+' 最终产物\n\nsummary.json / predictions.json.gz 是发布主结果。recorded-* 保留原运行指标；current-policy-* 是当前代码的离线复验，不能冒充新生成实验。FOLIO超时状态可能随机器负载变化，以summary中的冻结成绩为准。LogicalDeduction当前主分数来自原配套CoT的新版提取，standalone-cot是另一批新生成的独立CoT。\n')
        for config in ['run.json', 'plan.json']:
            if (source / config).exists():
                save(target / 'generation-config.json', load(source / config))
                break
        for filename in ['execution.jsonl', 'execution-events.jsonl', 'failures.json', 'failure.json', 'rejected-responses.jsonl', 'token-accounting-diagnosis.json']:
            if (source / filename).exists():
                save(target / 'logs' / (filename + '.gz'), (source / filename).read_text())
        if dataset == 'ProofWriter':
            for stage in ['program', 'cot']:
                save(target / 'logs' / (stage + '-run.json'), load(source / stage / 'run.json'))
        log_patterns = {'ProofWriter': ['proofwriter-full-launch.log'],
            'ProntoQA': ['full-ProntoQA-20261102.log', 'full-resume-ProntoQA-20261102.log'],
            'FOLIO': ['full-FOLIO-20261102.log'],
            'LogicalDeduction': ['ld-final-full-20261102.log', 'ld-final-full-resume-20261102.log'],
            'AR-LSAT': ['full-AR-LSAT-20261102.log', 'full-resume-AR-LSAT-20261102.log']}
        for filename in log_patterns[dataset]:
            path = ROOT / 'logs' / filename
            if path.exists():
                save(target / 'logs' / (filename + '.gz'), path.read_text())
        index['datasets'][dataset] = {'path': str(target.relative_to(ROOT)), 'n': load(current / 'summary.json')['n'], 'source_run_id': name, 'main_cot': 'paired original CoT; LogicalDeduction uses latest extraction only during current-policy replay', 'data_sha256': hashlib.sha256((UPSTREAM / f'data/{dataset}/dev.json').read_bytes()).hexdigest()}
    standalone = Path((ROOT / 'logs/ld-cot-full-current.txt').read_text())
    target = DEST / 'LogicalDeduction/standalone-cot'
    save(target / 'cot.json.gz', (standalone / 'cot.json').read_text())
    save(target / 'summary.json', load(standalone / 'summary.json'))
    save(target / 'generation-config.json', load(standalone / 'plan.json'))
    records = [load(p) for p in sorted((standalone / 'records').glob('*.json'))]
    save(target / 'cot-api.jsonl.gz', '\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\n')
    for path in [standalone / 'failures.json', ROOT / 'logs/ld-cot-full-20261102.log', ROOT / 'logs/ld-cot-full-resume-20261102.log']:
        if path.exists():
            save(target / 'logs' / (path.name + '.gz'), path.read_text())
    index['datasets']['LogicalDeduction']['standalone_cot'] = {'path': str(target.relative_to(ROOT)), 'source_run_id': standalone.name, 'n': 300, 'note': 'Separate fresh CoT-only run; not swapped into main paired answers.'}
    save(DEST / 'index.json', index)
    print('Exported 5 main runs and LogicalDeduction standalone CoT; raw credentials excluded.')


if __name__ == '__main__':
    main()
