"""Wait for graph import process, then launch a single end-to-end acceptance case."""
import os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
log=R/'.runtime/import-normalized.log'
while True:
 text=log.read_text(errors='replace') if log.exists() else ''
 if '金融知识图谱构建完成' in text:break
 if 'Traceback (most recent call last)' in text:raise RuntimeError('Graph import failed; inspect local log')
 time.sleep(5)
subprocess.run([sys.executable,str(R/'scripts/launch_smoke.py')],check=True)
