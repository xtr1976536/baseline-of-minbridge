from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];gold={'ProntoQA':83.20,'ProofWriter':79.66,'FOLIO':78.92,'LogicalDeduction':87.63,'AR-LSAT':43.04}
rows=['# 当前结果','\n仅为作者 GPT-4 逻辑程序的求解器重放；非端到端 API 复现。论文 Table 2 使用 CoT 回退，本次固定种子随机回退，结果不直接等价。','\n| 数据 | 样本 | 实测准确率 | 论文 GPT-4 | 差（百分点） | 求解失败 |','|---|---:|---:|---:|---:|---:|']
for name,v in gold.items():
 matches=list((root/'results').glob(f'logic-lm-{name}*summary.json'));f=max(matches,key=lambda p:p.stat().st_mtime) if matches else None
 if f:
  d=json.loads(f.read_text());acc=100*d['accuracy'];rows.append(f"| {name} | {d['n']} | {acc:.2f}% | {v:.2f}% | {acc-v:+.2f} | {d['solver_failures']} |")
rows+=['','LogicalDeduction 作者缓存只有 299 条。若全部求解失败，准确率仅由回退决定，不构成模型性能证据。','\nReAct：HotpotQA 7405 与 FEVER 9999 条 dev 数据加载、reset/finish 和评分接口已运行；500 样本主实验未调用模型。Wikipedia HTTP 403、作者 WebShop HTTP 502，须解决后执行。ALFWorld 安装与数据下载状态见日志。','\nAPI 待用户提供；原模型不可用时需确认替代模型并独立报告。']
(root/'docs/当前结果.md').write_text('\n'.join(rows))
