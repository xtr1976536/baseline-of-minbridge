"""Time-bounded trusted symbolic algebra, separate from the async event loop."""
import json
from pathlib import Path
import sys
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gbfr.graph import Formula,Operand,make_inverse

request=json.loads(sys.stdin.buffer.read().decode('utf-8'))
f=request['formula'];f['operands']=[Operand(**o) for o in f['operands']]
inverse=make_inverse(request['parent'],Formula(**f),request['name'],general=True)
print(json.dumps({'formula':asdict(inverse) if inverse else None},ensure_ascii=True))
