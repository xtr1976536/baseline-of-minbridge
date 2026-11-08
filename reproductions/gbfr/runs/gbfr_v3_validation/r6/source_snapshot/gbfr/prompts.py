"""Appendix F text extracted from the supplied PDF, with explicit slot filling.

The paper leaves {format} and {example} unresolved. The schemas below instantiate
the format slots. query_examples.txt supplies explicitly labelled local generic
examples; these are not represented as the authors' unpublished examples.
"""
from pathlib import Path

from .types import dumps


DIRECTORY = Path(__file__).with_name("prompts")
QUERY_EXAMPLES = (DIRECTORY / 'query_examples.txt').read_text(encoding='utf-8')


def _metric_pattern():
    """Positive regular language excluding only empty/placeholder names.

    The gateway supports ordinary regex but rejects lookarounds and `not`.
    A small trie expresses the same exclusion without restricting financial
    vocabulary, source labels, scripts or aliases.
    """
    tree={}
    for word in ('unknown','null','none','n/a','unspecified'):
        node=tree
        for char in word:node=node.setdefault(char,{})
        node['']=True
    branches=[]
    import re
    def walk(prefix,node):
        if prefix and '' not in node:branches.append(prefix)
        children=sorted(k for k in node if k)
        excluded=''.join(sorted({c for k in children for c in (k.lower(),k.upper())}))
        cls=re.escape(excluded)
        branches.append(prefix+'[^'+cls+r'\s]')
        if prefix:branches.append(prefix+('[^'+cls+']' if cls else r'[\s\S]')+r'[\s\S]*\S')
        else:branches.append('[^'+cls+r'\s][\s\S]*\S')
        for char in children:
            literal='['+char.upper()+char.lower()+']' if char.isalpha() else re.escape(char)
            walk(prefix+literal,node[char])
    walk('',tree)
    return '^(?:'+'|'.join(branches)+')$'


def _object(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


_nullable={'type':['string','null']}
PLAN_RESPONSE_FORMAT={'type':'json_schema','json_schema':{'name':'GBFRQuestionPlan','strict':True,
    'schema':_object({
        'reasoning_type':{'type':'string','enum':['DirectRetrieval','ArithmeticCalculation','ComparativeReasoning','StatisticalAggregation','TemporalReasoning']},
        'operator':{'type':'string','enum':['sum','difference','product','division','ratio','change ratio','range','compare','average','time','counting']},
        'subgoals':{'type':'array','minItems':1,'items':_object({
            'metric':{'type':'string','pattern':_metric_pattern(),
                      'description':'The actual requested numerical metric, using a source label or the appropriate canonical financial name. Never a placeholder.'},
            'constraints':_object({'temporal_scope':_nullable,'entity_scope':_nullable,
                                   'meta':_object({'currency':_nullable,'scale':_nullable,'unit':_nullable})})})},
        'precision':_nullable})}}

EVIDENCE_FORMAT = dumps({
    "found": True,
    "var_bindings": {"v1": {
        "metric": "requested metric", "constraints": {
            "temporal_scope": "copy input", "entity_scope": "copy input",
            "meta": {"currency": "copy input", "scale": "copy input", "unit": "copy input"}},
        "value": 123.0, "context": "source evidence showing the metric's own label and its printed number",
        "source_label":"copy the actual metric label or column header, not the entity/category row label",
        "observed_meta": {"currency": None, "scale": None, "unit": None},
        'context_spans': [],
        "confidence": 1.0,
    }}, "missing_vars": [], "notes": None,
}) + ('\nobserved_meta describes ONLY explicitly printed currency/scale/unit of the raw value; use null when unknown. '
      'Do not inherit a derived ratio unit onto a monetary input. Do not scale the extracted value.'
      ' Quote the source_label in its original language. Explain any clear alias or translation in notes, as required above. '
      'Never collapse adjusted/unadjusted, current/non-current or other financial qualifiers; a different known metric is not a semantic alias. '
      'For tables, copy the COMPLETE original header row and COMPLETE original data row into context_spans so their coordinate can be checked. '
      'Do not reorder columns, insert a year into a data row, abbreviate labels or omit intervening cells. Do not invent table titles. '
      'These may be separate source spans; typography, whitespace and Markdown need not be identical. '
      'Do not put another metric\'s value under the requested label. Never turn a formula result into extracted evidence. '
      'Scale is a multiplicative reporting unit such as thousand or million; shares, years and per-share describe unit, not scale. '
      'A raw dollar sign in the requested currency matches the same raw dollar sign in the source; do not demand a missing ISO code. '
      'Financial tables commonly print a currency sign once in the first monetary cell or a reporting header; that declaration applies to the same monetary column/table unless another currency is explicitly indicated. Do not require the sign to be repeated in every cell. '
      'If source_label differs from the requested metric, notes must explicitly explain the mapping, e.g. Resolved "Revenue" via alias "Net sales". '
      '\nNotes examples: requested Revenue, source "Revenue: 80" => notes=null; '
      'requested Revenue, source "Net sales: 80" => notes="Resolved Revenue via alias Net sales". '
      'If a contextual label omits qualifiers carried by a table title or heading, explain that contextual mapping in notes too. '
      '\nIf missing: {"found":false,"var_bindings":{},"missing_vars":["v1"],"notes":"reason"}')

VERIFY_FORMAT = dumps({"path_decisions": [{
    "path_id": "copy candidate path_id", "decision": "VALID or INVALID", "justification": "short reason",
}]}) + "\nReturn exactly one decision for EVERY supplied path, with no new paths or values."


def render(name: str, **slots) -> str:
    text = (DIRECTORY / (name + ".txt")).read_text(encoding="utf-8")
    # Single pass prevents evidence containing {query} etc. from becoming instructions.
    import re
    return re.sub(r"\{([a-z_]+)\}", lambda m: str(slots[m[1]]) if m[1] in slots else m[0], text)
