"""LogicalDeduction-only explicit CoT option extraction; no inference or gold access."""
import re
from logic_final import strip_markdown, cot_answer


def extract_ld_cot(raw, option_count):
    if option_count not in (3, 5, 7):
        raise ValueError('LogicalDeduction expects 3, 5 or 7 options')
    allowed = set('ABCDEFG'[:option_count])
    author = cot_answer(raw)
    # Author's explicit delimiter retains priority; otherwise inspect the original text.
    has_delimiter = 'The correct option is:' in raw
    text = strip_markdown(raw.split('The correct option is:')[-1] if has_delimiter else raw)
    candidates = re.findall(r'(?<![A-Za-z0-9])\(?([A-G])\)(?=\s|$)', text)
    candidates += re.findall(r'(?i:\b(?:the\s+)?(?:correct\s+)?(?:answer|option)\s*(?:is\s*:?|:)\s*)\(?([A-G])\b', text)
    if has_delimiter:
        match = re.match(r'^\(?([A-G])(?:\)|\.)?(?=\s|$)', text)
        if match:
            candidates.append(match[1])
    candidates = sorted(set(c.upper() for c in candidates))
    if any(c not in allowed for c in candidates):
        choice, reason = None, 'out_of_range'
    elif len(candidates) == 1:
        choice, reason = candidates[0], 'author_delimiter' if has_delimiter else 'unique_explicit_option'
    else:
        choice, reason = None, 'conflicting_options' if candidates else 'no_explicit_option'
    return {**author, 'markdown_only_predicted_answer': author['predicted_answer'],
            'predicted_answer': choice or '', 'cot_extraction': {'policy': 'ld-explicit-option-v1',
            'reason': reason, 'candidates': candidates, 'option_count': option_count}}
