"""Paper §4.2 metrics, with unresolved correctness retained in coverage."""
from __future__ import annotations
from decimal import Decimal
import re
from scipy.stats import beta
from .assets import scalar
from .grounding import conversion, Unresolved

def interval(k,n):
    if n == 0: return None
    return [0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)), 1.0 if k==n else float(beta.ppf(.975,k+1,n-k))]

def correctness(row, result):
    claimed = result.get('claimed_value')
    if claimed is None: return None
    gold = row['gold']
    value = scalar(gold['answer'])
    label_money_scale = None
    # Handle a single formatted amount conservatively; never select one of many.
    if value is None:
        text = str(gold['answer']).strip()
        m = re.fullmatch(r'\$?\s*([+-]?[\d,]+(?:\.\d+)?)\s*(million|billion|thousand)?\s*(?:USD|dollars)?',text,re.I)
        if m:
            value = m[1].replace(',','')
            if re.search(r'\$|usd|dollar',text,re.I):label_money_scale=m[2]
        else:
            # A unique explicitly marked amount/percentage is unambiguous even
            # inside a sentence. Never pick one of several competing targets.
            amounts=re.findall(r'\$\s*([+-]?[\d,]+(?:\.\d+)?)\s*(billion|million|thousand|bn|mn)?',text,re.I)
            percents=re.findall(r'([+-]?[\d,]+(?:\.\d+)?)\s*%',text)
            if len(amounts)==1 and not percents:
                value=amounts[0][0].replace(',','')
                label_money_scale=amounts[0][1]
            elif len(percents)==1 and not amounts:value=percents[0].replace(',','')
            else:return None
    unit = gold.get('unit')
    if row['dataset']=='TAT-DQA':
        scale = gold.get('scale','')
        if scale == 'percent': unit = 'percentage'
        elif scale in {'million','billion','thousand'}:
            # Currency is inferred only from the document's explicit disclosure.
            text = row['context'].lower()
            currency = 'USD' if re.search(r'\$|usd|u\.s\. dollars',text) else None
            if not currency: return None
            unit = currency+' '+scale
        elif scale=='':
            from verifiqa.answer_spec import answer_spec_from_question
            inferred=answer_spec_from_question(row['question']).expected_unit
            unit=inferred if inferred!='unspecified' else ('count' if re.search(r'how many',row['question'],re.I) else None)
    if unit is None:
        # Explicit units on the unique reference target precede question-wording
        # heuristics (e.g. "separation" is incorrectly classified as "ratio"
        # upstream). Unscaled dollar labels still inherit question magnitude.
        label=str(gold['answer']).lower()
        if '%' in label or 'percent' in label:unit='percentage'
        elif label_money_scale:
            unit='USD '+{'bn':'billion','mn':'million'}.get(label_money_scale.lower(),label_money_scale.lower())
    if unit is None:
        if re.search(r'\bdays?\s+(?:payable|sales|inventory)\s+outstanding\b|\bDPO\b|\bDSO\b',row['question'],re.I):
            unit='days'
    if unit is None:
        from verifiqa.answer_spec import answer_spec_from_question
        inferred=answer_spec_from_question(row['question']).expected_unit
        if inferred!='unspecified':unit=inferred
    if unit is None:
        answer = str(gold['answer']).lower()
        if '%' in answer or 'percent' in answer: unit='percentage'
        elif 'ratio' in answer or answer.endswith('x'): unit='ratio'
        elif re.search(r'\$|usd|dollar',answer):
            scale = next((x for x in ['million','billion','thousand'] if x in answer),'million' if re.search(r'\d\s*mn\b',answer) else ('billion' if re.search(r'\d\s*bn\b',answer) else ''))
            unit='USD '+scale
        elif scalar(gold['answer']) is not None:
            # Scalar labels without declared units remain unresolved for FB.
            return None
        else: return None
    try:
        expected = Decimal(value)*conversion(unit,result['claimed_unit'])
    except Unresolved: return None
    # Evaluation is separate from verifier tolerance. Use label display precision.
    digits = max(0,-Decimal(value).as_tuple().exponent)
    tolerance = Decimal('.5')*(Decimal(10)**-digits)*abs(conversion(unit,result['claimed_unit']))
    return abs(Decimal(claimed)-expected) <= tolerance

def summarize(rows, n):
    counts = dict.fromkeys(['TA','FA','TR','FR','Abs','unresolved_decided','errors','missing'],0)
    seen = set()
    for r in rows:
        if r['id'] in seen: raise ValueError('duplicate_prediction_id')
        seen.add(r['id'])
        status = r['result']['status']
        if status == 'ERROR': counts['errors']+=1; continue
        if status == 'ABSTAIN': counts['Abs']+=1; continue
        correct = r.get('correct')
        if correct is None: counts['unresolved_decided']+=1; continue
        counts[('TA' if correct else 'FA') if status=='VERIFIED' else ('FR' if correct else 'TR')]+=1
    counts['missing'] = n-len(rows)
    if counts['missing'] < 0: raise ValueError('too_many_predictions')
    decided = counts['TA']+counts['FA']+counts['TR']+counts['FR']
    accepted = counts['TA']+counts['FA']
    covered = decided+counts['unresolved_decided']
    complete = counts['missing']==0 and counts['errors']==0
    return {**counts,'N':n,'complete':complete,
            'precision':counts['TA']/accepted if accepted else None,
            'accuracy':(counts['TA']+counts['TR'])/decided if decided else None,
            'coverage':covered/n if n else None, 'abstention_rate':counts['Abs']/n if n else None,
            'precision_ci95':interval(counts['TA'],accepted),
            'accuracy_ci95':interval(counts['TA']+counts['TR'],decided),
            'coverage_ci95':interval(covered,n)}
