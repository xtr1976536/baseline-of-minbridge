"""生成 Logic-LM 官方 CoT 回退答案（仅用于主模型失败样本）。"""
import argparse, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_compat import generate

p = argparse.ArgumentParser()
p.add_argument('--dataset', required=True, choices=['ProntoQA','ProofWriter','FOLIO','LogicalDeduction','AR-LSAT'])
p.add_argument('--model', default='gpt-4', help='作者参考模型标签；用于保留官方 prompt 命名')
p.add_argument('--api-model', help='API 实际模型 ID；默认与 --model 相同')
p.add_argument('--api-style', choices=['auto','completion','chat'], default='auto')
p.add_argument('--limit', type=int)
p.add_argument('--max-tokens', type=int, default=1024)
p.add_argument('--split', choices=['dev','test'], default='dev')
a = p.parse_args()
if not os.getenv('OPENAI_API_KEY'):
    raise SystemExit('缺少 OPENAI_API_KEY；未发出请求。')

u = ROOT / 'upstream/Logic-LLM'
sys.path.insert(0, str(u / 'baselines'))
from gpt3_baseline import GPT3_Reasoning_Graph_Baseline
from types import SimpleNamespace
args = SimpleNamespace(data_path=str(u/'data'), dataset_name=a.dataset, split=a.split,
    model_name=a.model, save_path='', demonstration_path=str(u/'baselines/icl_examples'),
    api_key=os.environ['OPENAI_API_KEY'], stop_words='------', mode='CoT', max_new_tokens=a.max_tokens)
baseline = GPT3_Reasoning_Graph_Baseline(args)
cot_prompt = (u/'baselines/icl_examples'/f'{a.dataset}_CoT.txt').read_text()
baseline.load_in_context_examples = lambda: cot_prompt
rows = baseline.load_raw_dataset(a.split)
rows = rows[:a.limit] if a.limit else rows
examples = baseline.load_in_context_examples()
run = ROOT/'results'/f'logic-cot-{a.dataset}-{a.split}-{(a.api_model or a.model).replace("/", "_")}-{int(time.time())}'
run.mkdir(parents=True)
predictions = []
api_log = (run/'api.jsonl').open('a')
for e in rows:
    prompt = baseline.prompt_creator(examples, e)
    raw, response, style, wire_model = generate(prompt, a.model, a.api_model, a.api_style,
        a.max_tokens, 0.0, '------', 120)
    predictions.append({'id':e['id'], 'question':e['question'], 'answer':e['answer'],
        'predicted_reasoning':raw.split(baseline.label_phrase)[0].strip(),
        'predicted_answer':raw.split(baseline.label_phrase)[-1].strip(),
        'raw_output':raw})
    api_log.write(json.dumps({'id':e['id'],'prompt':prompt,'response':response,
            'reference_model':a.model,'api_model':wire_model,'api_style':style},ensure_ascii=False)+'\n')
    api_log.flush()
    (run/'cot.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2))
api_log.close()
(run/'run.json').write_text(json.dumps({'dataset':a.dataset,'split':a.split,'n_requested':len(rows),
    'purpose':'Logic-LM solver-failure fallback; official CoT prompt/examples',
    'reference_model':a.model,'api_model':a.api_model or a.model,'api_style':a.api_style,
    'temperature':0,'max_tokens':a.max_tokens,'top_p':1.0,'stop':'------',
    'result_class':'reference_model' if a.model==(a.api_model or a.model) else 'substitute_backbone'},ensure_ascii=False,indent=2))
print(run/'cot.json')
