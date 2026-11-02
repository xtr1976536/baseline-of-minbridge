"""Final Logic-LM policy: unchanged author solver, one format prefix, Markdown-only CoT cleanup."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'upstream/Logic-LLM'
DATASETS = ('ProntoQA', 'ProofWriter', 'FOLIO', 'LogicalDeduction', 'AR-LSAT')
FORMAT_FILE = ROOT / 'configs/prompts/logic-format-minimal.txt'
LOGICAL_DEDUCTION_FORMAT_FILE = ROOT / 'configs/prompts/LogicalDeduction-format-minimal.txt'
AR_LSAT_FORMAT_FILE = ROOT / 'configs/prompts/AR-LSAT-format-minimal.txt'
PAPER = {
    'ProntoQA': {'accuracy': .832, 'executable_rate': 1., 'executable_accuracy': .832, 'cot_accuracy': .9879},
    'ProofWriter': {'accuracy': .7966, 'executable_rate': .99, 'executable_accuracy': .796, 'cot_accuracy': .6811},
    'FOLIO': {'accuracy': .7892, 'executable_rate': .799, 'executable_accuracy': .804, 'cot_accuracy': .7058},
    'LogicalDeduction': {'accuracy': .8763, 'executable_rate': 1., 'executable_accuracy': .876, 'cot_accuracy': .7525},
    'AR-LSAT': {'accuracy': .4304, 'executable_rate': .326, 'executable_accuracy': .600, 'cot_accuracy': .3506},
}


def strip_markdown(text):
    """Remove display markup only; never infer an option from reasoning or gold labels."""
    text = text or ''
    text = re.sub(r'^\s*```[^\n]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*(?:>\s*|[-+*]\s+)', '', text, flags=re.MULTILINE)
    text = text.replace('`', '').replace('*', '')
    # Remove underscore emphasis without corrupting words_with_underscores.
    text = re.sub(r'(?<!\w)_{1,2}(?=\S)|(?<=\S)_{1,2}(?!\w)', '', text)
    return text.strip()


def cot_answer(raw):
    # Exactly the author's label phrase split, followed only by display cleanup.
    answer = raw.split('The correct option is:')[-1].strip()
    return {'raw_predicted_answer': answer, 'predicted_answer': strip_markdown(answer),
            'predicted_reasoning': raw.split('The correct option is:')[0].strip(), 'raw_output': raw}


def format_constraint(dataset):
    path = {'LogicalDeduction': LOGICAL_DEDUCTION_FORMAT_FILE, 'AR-LSAT': AR_LSAT_FORMAT_FILE}.get(dataset, FORMAT_FILE)
    return path.read_text().strip()

def prompt_files(dataset):
    name = 'AR-LSAT-long' if dataset == 'AR-LSAT' else dataset
    return (UPSTREAM / f'models/prompts/{name}.txt',
            UPSTREAM / f'baselines/icl_examples/{dataset}_CoT.txt')


def build_prompt(dataset, stage, row):
    program, cot = prompt_files(dataset)
    if stage == 'program':
        text = program.read_text().replace('[[PROBLEM]]', row['context']).replace('[[QUESTION]]', row['question'].strip())
        if dataset in ('LogicalDeduction', 'AR-LSAT'):
            choices = '\n'.join(f'({choice.strip()}' for choice in row['options']).strip()
            text = text.replace('[[CHOICES]]', choices)
        return format_constraint(dataset) + '\n\n' + text
    if stage != 'cot':
        raise ValueError(stage)
    return (cot.read_text().replace('[[CONTEXT]]', row['context'].strip())
            .replace('[[QUESTION]]', row['question'].strip())
            .replace('[[OPTIONS]]', '\n'.join(opt.strip() for opt in row['options'])))


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    tmp.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_rows(rows, expected, complete=True):
    lookup = {row['id']: row for row in expected}
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) - set(lookup) or (complete and set(ids) != set(lookup)):
        raise ValueError('Duplicate, foreign, or missing sample IDs')
    for row in rows:
        for key in ('context', 'question', 'answer', 'options'):
            if key in row and row[key] != lookup[row['id']][key]:
                raise ValueError(f'Dataset mismatch: {row["id"]} / {key}')


def raw_cot_answer(row):
    if 'raw_output' in row:
        return row['raw_output'].split('The correct option is:')[-1].strip()
    return row.get('raw_predicted_answer', row['predicted_answer'])


def check_runtime(dataset):
    """Fail before paid calls if a required solver binary is absent/unexecutable."""
    import os
    import subprocess
    if dataset == 'FOLIO':
        directory = os.getenv('PROVER9_BIN')
        env_file = ROOT / '.local/prover9.env'
        if not directory and env_file.exists():
            directory = env_file.read_text().strip().split('=', 1)[1]
        binary = Path(directory) / 'prover9' if directory else UPSTREAM / 'models/symbolic_solvers/Prover9/bin/prover9'
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise RuntimeError('Prover9 unavailable; run bash scripts/build_prover9.sh before API generation')
        try:
            subprocess.run([str(binary), '-h'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except OSError as ex:
            raise RuntimeError('Prover9 binary is incompatible; rebuild with scripts/build_prover9.sh') from ex
    if dataset == 'AR-LSAT':
        import z3  # noqa: F401 - fail early on a missing runtime
    elif dataset == 'LogicalDeduction':
        import constraint  # noqa: F401
    elif dataset in ('ProntoQA', 'ProofWriter'):
        import pyke  # noqa: F401
