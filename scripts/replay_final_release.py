"""Replay released model outputs with author solvers. Offline; never calls model APIs."""
import argparse
import gzip
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from logic_final import ROOT, DATASETS


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',choices=DATASETS,required=True)
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args();folder=ROOT/'experiments/final'/args.dataset
    output=(args.output_dir or ROOT/'.local/release-replay'/args.dataset).resolve()
    with tempfile.TemporaryDirectory(prefix='minbridge-replay-') as temporary:
        temporary=Path(temporary)
        for name in ['programs.json','cot.json']:
            (temporary/name).write_bytes(gzip.decompress((folder/(name+'.gz')).read_bytes()))
        subprocess.run([sys.executable,str(ROOT/'scripts/evaluate_logic_experiment.py'),'--dataset',args.dataset,
            '--programs',str(temporary/'programs.json'),'--cot',str(temporary/'cot.json'),
            '--output-dir',str(output)],cwd=ROOT,check=True)
    actual=json.loads((output/'summary.json').read_text());expected=json.loads((folder/'summary.json').read_text())
    differences={key:{'released':expected[key],'replay':actual[key]} for key in
        ('accuracy','executable_rate','executable_accuracy','cot_accuracy') if actual[key]!=expected[key]}
    (output/'release-comparison.json').write_text(json.dumps({'dataset':args.dataset,'differences':differences,
        'note':'Prover9/Z3 resource/time limits can produce execution-status variation. Recorded release artifacts are never overwritten.'},indent=2))
    print('Replay saved to',output,'; differences:',differences)

if __name__=='__main__':main()
