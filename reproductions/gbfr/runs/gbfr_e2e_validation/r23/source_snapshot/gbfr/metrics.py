"""Section 5.1: numerical normalization, explicit resolution and abstention recall."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re


SCALES = {"": 1, "unknown": 1, "none": 1, "ones": 1, "unit": 1, "units": 1,
          "thousand": 1000, "thousands": 1000, "千": 1000,
          "million": 10**6, "millions": 10**6, "百万": 10**6,
          "billion": 10**9, "billions": 10**9, "十亿": 10**9,
          "万": 10**4, "万元": 10**4, "亿": 10**8, "亿元": 10**8, "万亿": 10**12}
PERCENT_UNITS = {"%", "percent", "percentage", "百分比", "百分数"}
RATIO_UNITS = {"ratio", "decimal", "rate", "fraction", "比例"}
BASE_CURRENCY_SCALES={'yuan':'CNY','rmb':'CNY','cny':'CNY','人民币':'CNY','人民币元':'CNY',
                      'usd':'USD','美元':'USD','eur':'EUR','euro':'EUR','euros':'EUR',
                      'gbp':'GBP','英镑':'GBP','jpy':'JPY','日元':'JPY','hkd':'HKD','港元':'HKD'}


@dataclass
class Number:
    value: Decimal
    meta: dict


def parse_number(answer) -> Number | None:
    if isinstance(answer, bool) or answer is None or isinstance(answer, (list, dict)):
        return None
    if isinstance(answer, (int, float)):
        result = Decimal(str(answer))
        return Number(result, {}) if result.is_finite() else None
    text = str(answer).strip().replace("−", "-").replace("％", "%")
    currency = None
    direction = 1
    if text.casefold().startswith("decreased "):
        text, direction = text[len("decreased "):].strip(), -1
    # A labelled monetary scalar still contains one value, e.g. the published
    # TAT-QA answer "United States non-current assets of $182.4 million". Match
    # the entire label + quantity, preserve the label, and never choose the first
    # number of a sentence with years, ratios, or multiple financial quantities.
    labelled = re.fullmatch(r"([A-Za-z][A-Za-z ,()'/-]+?)\s+of\s+((?:US\$|\$|£|€|¥|￥).+)", text)
    if labelled:
        amount = parse_number(labelled[2])
        if amount is not None and amount.meta.get("currency"):
            amount.value *= direction
            amount.meta["label"] = labelled[1].strip()
            return amount
    for marker, name in [("US$", "USD"), ("$", "USD"), ("£", "GBP"), ("€", "EUR"), ("¥", "CNY"), ("￥", "CNY")]:
        if text.startswith(marker):
            text, currency = text[len(marker):].strip(), name
            break
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    # Whitelist full scalar answers, not the first number of a text span or a year list.
    match = re.fullmatch(
        r"([+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
        r"\s*(%|percent|percentage|thousand|million|billion|"
        r"(?:万亿|千|万|亿)?(?:元|美元|股|份|吨|平方米)|千|万|亿|元[/／](?:桶|股)|美元[/／]桶|"
        r"个?百分点|年|天|次|手|倍|只|GW|shares|grants|times|x)?", text,
        flags=re.I)
    if not match:
        return None
    try:
        value = Decimal(match[1].replace(",", ""))
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    if negative:
        value = -value
    value *= direction
    suffix = (match[2] or "").lower()
    meta = {}
    if currency:
        meta["currency"] = currency
    if suffix in PERCENT_UNITS:
        meta["unit"] = "percentage"
    elif suffix in SCALES and suffix:
        meta["scale"] = suffix
    elif suffix in {"百分点", "个百分点"}:
        meta["unit"] = "percentage"
    elif suffix in {'x','times'}:meta['unit']='ratio'
    elif suffix:
        scale = re.match(r"^(万亿|千|万|亿)(.+)$", suffix)
        if scale:
            meta.update(scale=scale[1], unit=scale[2])
        else:
            meta["unit"] = suffix
    return Number(value, meta)


def normalized(value, meta: dict) -> tuple[float, tuple]:
    amount, dimension = canonical(Decimal(str(value)), meta)
    return float(amount), dimension


def canonical(value: Decimal, meta: dict) -> tuple[Decimal, tuple]:
    from .units import FACTORS,normalize_meta
    m=normalize_meta(meta)
    value *= FACTORS[m['scale'] or '']
    unit=m['unit'] or ''
    if unit=='percentage':
        value /= 100
        unit = "ratio"
    return value,(m['currency'] or '',unit)


def precision_from_query(query: str) -> int | None:
    query = query.casefold()
    if any(t in query for t in ["nearest integer", "nearest whole", "保留整数", "四舍五入到整数"]):
        return 0
    if any(t in query for t in ["nearest cent", "closest cent"]):
        return 2
    if any(t in query for t in ["nearest dollar", "closest dollar"]):
        return 0
    words = {"zero": 0, "one": 1, "single": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6}
    match = re.search(r"(\d+|zero|one|single|two|three|four|five|six)\s+decimal\s+places?", query)
    if not match:
        match = re.search(r"保留\s*([0-9一二两三四五六]+)\s*位(?:小数)?", query)
    if match:
        raw = match[1]
        result = int(raw) if raw.isdigit() else words.get(raw)
        if result is not None and 0 <= result <= 12:
            return result
    return None


def correct(prediction: dict, sample: dict, unspecified_decimals: int = 2, precision_policy='fixed') -> bool:
    if sample["unanswerable"]:
        return prediction.get("status") == "abstained"
    if prediction.get("status") != "answered":
        return False
    if sample.get("dataset") == "FinanceReasoning" and sample.get("answer_type") == "boolean":
        expected = sample["answer"]
        value = prediction.get("value")
        return (isinstance(expected, bool) and type(value) in {int, float}
                and prediction.get("meta", {}).get("unit") == "boolean"
                and value in {0, 1} and bool(value) == expected)
    expected = parse_number(sample["answer"])
    actual = parse_number(prediction.get("value"))
    if expected is None or actual is None:
        return False
    from .units import known,normalize_meta,target_meta
    try:
        gold_meta=target_meta(sample,expected.meta)
        pred_meta=normalize_meta(prediction.get('meta',{}))
        # A total monetary value and a per-security price are different output
        # quantities even if their displayed numbers happen to be identical.
        if (gold_meta['unit'] is None and pred_meta['unit'] in {'currency/share','currency/warrant'}
                and re.search(r'\b(?:total|aggregate|combined)\s+(?:value|amount|cost|expense|proceeds)\b',sample['question'],re.I)):
            return False
        if gold_meta['unit']=='count':
            # "How many years satisfied condition X?" asks for a cardinality,
            # not a time duration. A label "years" and a label "count" refer
            # to the same output only when the query names that counted unit.
            counted=pred_meta['unit']
            if counted in {'years','quarters','months'} and re.search(
                    r'\bhow\s+many\s+(?:(?:fiscal|calendar)\s+)?'+counted+r'\b',sample['question'],re.I):
                pred_meta['unit']='count'
            if known(pred_meta['currency']) or pred_meta['scale'] not in {None,'ones'}:
                return False
        # Appendix F requires a numeric value and trace, not output_meta.
        # A bare output is in the task's display unit. Explicit metadata takes
        # precedence and is converted, never searched for a factor that fits.
        pred_meta={k:pred_meta[k] if known(pred_meta[k]) else gold_meta[k] for k in ('currency','scale','unit')}
        gold, gold_dim = canonical(expected.value, gold_meta)
        pred, pred_dim = canonical(actual.value,pred_meta)
    except ValueError:
        return False
    # A native bare scalar with no source unit is a display number, not a
    # claim that its physical scale equals one. No factor conversion is guessed.
    unknown_display=not any(known(v) for v in gold_meta.values())
    if unknown_display:
        gold,pred=expected.value,actual.value
        gold_dim=pred_dim=('','')
    # Unknown metadata cannot justify a conversion. Known incompatible dimensions fail.
    if any(a and b and a != b for a, b in zip(gold_dim, pred_dim)):
        return False
    if (gold_dim[1] == "ratio") != (pred_dim[1] == "ratio"):return False
    # Quantize in the GOLD DISPLAY UNIT, not in ratio/base-currency units.
    display_factor, _ = canonical(Decimal(1), gold_meta)
    places = precision_from_query(sample["question"])
    if places is None:
        if precision_policy=='reference_display':
            # The reference fixes the reported resolution independently of
            # the prediction. FinQA often publishes one decimal place; adding
            # an artificial second place rejects a mathematically correct
            # unrounded executor result. Explicit query precision wins above.
            places=max(0,-expected.value.as_tuple().exponent)
        elif precision_policy=='fixed':places=unspecified_decimals
        else:raise ValueError('Unknown precision policy')
    quantum = Decimal(1).scaleb(-places)
    try:
        with localcontext() as ctx:
            ctx.prec = 80
            return (gold / display_factor).quantize(quantum, rounding=ROUND_HALF_UP) == (
                pred / display_factor).quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return False


def summarize(samples: list[dict], predictions: list[dict], unspecified_decimals: int = 2, precision_policy='fixed') -> dict:
    by_id = {p["sample_id"]: p for p in predictions}
    if len(by_id) != len(predictions):
        raise ValueError("Duplicate predictions")
    ids = {s["id"] for s in samples}
    if len(ids) != len(samples) or set(by_id) - ids:
        raise ValueError("Duplicate sample ids or predictions outside evaluation set")
    scores = [(s, correct(by_id.get(s["id"], {}), s, unspecified_decimals,precision_policy)) for s in samples]
    n = len(samples)
    negatives = sum(s["unanswerable"] for s in samples)
    good_negative = sum(ok for s, ok in scores if s["unanswerable"])
    return {"n": n, "predictions": len(predictions), "missing": n-len(predictions),
            "errors": sum(p.get("status") == "error" for p in predictions),
            "correct": sum(ok for _, ok in scores), "unanswerable": negatives,
            "correct_abstentions": good_negative,
            "total_accuracy": 100*sum(ok for _, ok in scores)/n if n else None,
            "abstention_accuracy": 100*good_negative/negatives if negatives else None,
            "complete": len(predictions) == n and not any(p.get("status") == "error" for p in predictions)}
