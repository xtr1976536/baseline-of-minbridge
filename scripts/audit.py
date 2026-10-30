"""记录输入校验和和固定版本，不输出密钥。"""
from pathlib import Path
import hashlib,json,platform,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];records=[]
for name in ['ReAct','Logic-LLM']:
 p=ROOT/'upstream'/name;commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()
 for f in sorted(p.rglob('*')):
  if f.is_file() and '.git' not in f.parts and f.suffix in ['.json','.jsonl','.ipynb'] and not any(x.startswith('.cache') for x in f.parts):
   records.append({'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'upstream_commit':commit})
(ROOT/'manifests/inputs.json').write_text(json.dumps(records,indent=2));(ROOT/'manifests/environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform()},indent=2));print('manifest entries',len(records))
