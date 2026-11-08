"""One question/evidence-only planning call; no substring-based shortcut plans."""
from __future__ import annotations
import json
import re
from verifiqa.agent.types import ClaimSpec,RoleSpec
from verifiqa.agent.utils import extract_json
from verifiqa.agent.claim_classifier import _format_registry
from verifiqa.generation.llm_client import ChatMessage


PROMPT='''Build a verification plan for the financial question using only the question,
the filing evidence and the documented registry below. No proposed answer is available.

Resolve the actual target in the main question before interpreting its definitions.
An internal "change in inventory" is not the whole DPO task. A margin change needs
the two margins expanded into income/revenue operands. An average of margins needs
each period's ratio, not an average of all monetary leaves. For nested definitions
(CCC, DIO, DSO, DPO), substitute the explicit definitions into a complete leaf formula.
List only primitive required operands with their exact periods and filing row aliases.
Do not list a derived average/margin as a primitive tagged fact unless it is explicitly
reported. Do not invent an undocumented formula. Explicit question equations take
priority over standard conventions. Preserve source-qualified net/gross/attributable,
cash/noncash and per-share meanings. Shares, USD, percentages and days are distinct.
Missing evidence does not make a numerical question qualitative. If the question or
registry establishes a numerical operation, still list its required primitive roles;
the provenance verifier, not this planner, will decide if their filed facts exist.
For a requested reported line item, provide its identity role instead of a constant
zero. An "if absent, state zero" instruction is not proof that a line item is absent.
If a question asks only for a name, purpose or qualitative outcome, mark unverifiable;
do not turn it into a made-up scalar lookup. Never fill missing values from knowledge.

Return JSON only:
{{"verifiable":true,"metric":"snake_case target","formula":"arithmetic leaf formula",
"roles":[{{"name":"variable","aliases":["filing row label"],"period":"FY2020 or Q2 2023"}}],
"claim_unit":"USD millions|USD billions|USD per share|percent|ratio|days|count",
"formula_source":"policy_registry|generic_operation|document_derived|no_formula"}}
Use verifiable=false, formula="", roles=[] when no numerical target can be established.
Registry:
{registry}
Question: {question}
Filing evidence:
{evidence}
'''


def decompose_question(question,llm_client,evidence_text='',**kwargs):
    raw=llm_client.chat([ChatMessage('user',PROMPT.format(registry=_format_registry(),question=question,evidence=evidence_text))],stage='question_decomposition')
    data=json.loads(extract_json(raw));years=re.findall(r'(?:19|20)\d{2}',question)
    if str(data.get('verifiable',True)).lower()=='false':
        return ClaimSpec(str(data.get('metric','unknown')),'',[],str(data.get('claim_unit','')),0,'no_formula')
    roles=[RoleSpec(str(r['name']),[str(a) for a in r.get('aliases',[])],str(r.get('period',''))) for r in data.get('roles',[]) if r.get('name')]
    return ClaimSpec(str(data.get('metric','unknown')),str(data.get('formula','')),roles,
                     str(data.get('claim_unit','')),0,str(data.get('formula_source','no_formula')),
                     years[-1] if years else '')
