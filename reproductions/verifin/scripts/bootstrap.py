"""Acquire the pinned public source; never run archived experiments."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
COMMIT='5c49943e8aa43f3dc03c1b2058a73469b22c5c5e'
upstream=ROOT/'upstream'
if not upstream.exists():
    subprocess.run(['git','clone','--filter=blob:none','https://github.com/verifiedfinance/anon.git',str(upstream)],check=True)
    subprocess.run(['git','checkout','--detach',COMMIT],cwd=upstream,check=True)
actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()
if actual!=COMMIT:raise SystemExit('Upstream revision differs from pinned source; use a separate clone')
print('Pinned upstream ready:',COMMIT)
print('Install with this Python, then prepare:')
print(sys.executable,'-m pip install -e',str(upstream))
print(sys.executable,'-m pip install -e',str(ROOT))
