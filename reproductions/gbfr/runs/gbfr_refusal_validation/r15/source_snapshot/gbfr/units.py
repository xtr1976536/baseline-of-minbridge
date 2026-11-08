"""Source-based display units shared by grounding, execution and evaluation.

Unknown units are not silently asserted to be base currency. No function in this
module uses a model prediction to choose a gold unit or a conversion factor.
"""
from __future__ import annotations
import html
import re

FACTORS={'':1,'ones':1,'thousand':1000,'million':10**6,'billion':10**9,
         'trillion':10**12,'lakh':10**5,'crore':10**7,'千':1000,'万':10**4,
         '百万':10**6,'亿':10**8,'十亿':10**9,'万亿':10**12}
CURRENCIES={'$':'USD','us$':'USD','u.s. dollars':'USD','dollars':'USD','dollar':'USD',
            'usd':'USD','£':'GBP','gbp':'GBP','pounds':'GBP','€':'EUR','eur':'EUR',
            '¥':'CNY','￥':'CNY','yuan':'CNY','rmb':'CNY','cny':'CNY','元':'CNY',
            '人民币':'CNY','人民币元':'CNY','美元':'USD','jpy':'JPY','hkd':'HKD',
            'a$':'AUD','au$':'AUD','aud':'AUD','hk$':'HKD','s$':'SGD','sgd':'SGD',
            'singapore dollars':'SGD','英镑':'GBP','日元':'JPY'}
PERCENT={'%','percent','percentage','百分比','百分数','percentage point','percentage points','百分点','个百分点'}
RATIO={'ratio','decimal','rate','fraction','比例','times','multiple','倍'}
MONEY={'currency','monetary','money','amount','amounts','currency amount','monetary amount','cash proceeds',
       'dollar','dollars','usd','cny','yuan','rmb','元','美元','number','numeric'}
COUNTS={'share':'shares','shares':'shares','warrant':'warrants','warrants':'warrants',
        'year':'years','years':'years','day':'days','days':'days','square feet':'square feet',
        'sq. ft.':'square feet','sq ft':'square feet','barrels per day':'barrels/day',
        'barrels/day':'barrels/day','barrels':'barrels','employees':'employees','count':'count'}

def known(value):return value is not None and str(value).strip().casefold() not in {'','none','unknown','null','n/a'}

def unit_name(value):
    if not known(value):return None
    text=' '.join(str(value).casefold().replace('_',' ').split())
    if text in PERCENT:return 'percentage'
    if text in RATIO:return 'ratio'
    if text in MONEY:return None
    if text in COUNTS:return COUNTS[text]
    if text in {'per share','currency per share','dollars per share','share price','price per share','元/股','元／股'}:return 'currency/share'
    if re.fullmatch(r'(?:usd|gbp|eur|cny|sgd|aud|hkd|cad|nzd|jpy|us\$|s\$|\$|£|€|¥)\s*(?:/|per)\s*share',text):return 'currency/share'
    if text in {'price','currency/unit'}:return 'currency/unit'
    return text

def normalize_meta(meta: dict | None) -> dict:
    if meta is None:meta={}
    if not isinstance(meta,dict):raise ValueError('Unit metadata must be an object')
    raw_currency=meta.get('currency')
    currency=CURRENCIES.get(str(raw_currency).strip().casefold(),str(raw_currency).strip().upper()) if known(raw_currency) else None
    unit=unit_name(meta.get('unit'))
    raw_scale=meta.get('scale')
    scale=' '.join(str(raw_scale).casefold().replace('’',"'").split()) if known(raw_scale) else ''
    prefix=re.match(r'^(us\$|a\$|hk\$|\$|£|€|usd|gbp|eur|dollars?)',scale)
    if prefix and not currency:currency=CURRENCIES.get(prefix[1])
    if scale in CURRENCIES:
        implied=CURRENCIES[scale]
        if currency and currency!=implied:raise ValueError('Currency conflicts with scale label')
        currency=currency or implied;scale=''
    elif scale in {'unit','units','1','unscaled','actual','actuals'}:scale='ones'
    elif scale in PERCENT:
        if unit not in {None,'percentage'}:raise ValueError('Conflicting percentage unit')
        unit='percentage';scale=''
    elif scale in COUNTS or scale in {'per share','currency per share','share price'}:
        implied=unit_name(scale)
        if unit in {None,'currency/unit'}:unit=implied
        scale=''
    else:
        # Reporting phrases are format variants, not new numerical assumptions.
        scale=re.sub(r'^(?:amounts?\s+|dollars?\s+|usd\s+|us\$\s*|\$\s*|£\s*|€\s*)?(?:in\s+)?','',scale)
        short={"'000":'thousand','000':'thousand',"000's":'thousand',"'000s":'thousand',
               '000s':'thousand','k':'thousand','m':'million','mn':'million','mm':'million','mil':'million',
               'b':'billion','bn':'billion','bil':'billion','tn':'trillion','万元':'万','亿元':'亿',
               '1000':'thousand','1000000':'million','1000000000':'billion'}
        scale=short.get(scale,scale)
        match=re.fullmatch(r'(thousands?|millions?|billions?|trillions?|lakhs?|crores?)(?:\s+(?:of\s+)?(.+))?',scale)
        if match:
            scale=match[1].rstrip('s')
            if match[2] and unit is None:unit=unit_name(match[2])
    if scale not in FACTORS:raise ValueError('Unsupported scale: '+str(raw_scale))
    return {'currency':currency,'scale':scale or None,'unit':unit}

def reporting_meta(context: str) -> dict:
    """Only explicit reporting declarations, not arbitrary inline amounts."""
    text=html.unescape(re.sub(r'<[^>]+>',' ',context)).replace('’',"'")
    found=[]
    patterns=[r'(?P<currency>US\$|A\$|HK\$|\$|£|€|USD|GBP|EUR)?\s*(?:dollars?\s+)?\bin\s+(?:(?P<after_currency>US\$|A\$|HK\$|\$|£|€|USD|GBP|EUR)\s*)?(?P<scale>thousands?|millions?|billions?|lakhs?|crores?)\b',
              r'(?P<currency>US\$|A\$|HK\$|\$|£|€)\s*(?P<scale>\x27000s?|000s?|mn|mm|m|bn)\b',
              r'amounts?\s+(?:are\s+)?(?P<currency>USD|GBP|EUR|US\$|\$|£|€)\s+(?P<scale>thousands?|millions?|billions?)\b']
    for pattern in patterns:
        for match in re.finditer(pattern,text,re.I):
            found.append(normalize_meta({'currency':match['currency'] or match.groupdict().get('after_currency'),'scale':match['scale']}))
    scales={m['scale'] for m in found};currencies={m['currency'] for m in found if m['currency']}
    return {'scale':next(iter(scales)) if len(scales)==1 else None,
            'currency':next(iter(currencies)) if len(currencies)==1 else None,'unit':None}


def result_meta(meta,operator=None,*,query=None):
    """Derive output dimensions, never a numeric correction or guessed factor.

    A ratio/percentage has no residual currency or monetary reporting scale.
    Keeping USD millions inherited from the operands would multiply a correct
    percentage by a million at evaluation and in cross-path consensus.
    """
    result=normalize_meta(meta)
    if result['unit'] in {'ratio','percentage'} or operator in {'ratio','change ratio'}:
        result.update(currency=None,scale=None)
    # Selection returns a period identifier, not the financial magnitude that
    # was compared. This depends only on the explicit output request; never on
    # the result's numeric size or the reference answer.
    if operator in {'compare','time'} and query and re.search(
            r"\b(?:which|what)\s+(?:fiscal\s+|calendar\s+)?year\b(?!\s*[-–]\s*over\b|['’]s\b)",query,re.I):
        result.update(currency=None,scale=None,unit='years')
    return result

def target_meta(sample: dict, label_meta: dict) -> dict:
    """Gold display contract from official labels, question and source headers."""
    native={**label_meta,**sample.get('answer_meta',{})}
    meta=normalize_meta(native)
    q=sample['question'].casefold()
    explicit=re.search(r'\b(?:answer(?:ed)?|express(?:ed)?|report(?:ed)?|give|calculate)?\s*\bin\s+(thousands?|millions?|billions?|lakhs?|crores?)\b',q)
    if explicit:meta['scale']=normalize_meta({'scale':explicit[1]})['scale']
    if re.search(r'\b(?:percent(?:age)?|percentage points?)\b',q) and meta['unit'] is None:
        meta.update(unit='percentage',scale=None,currency=None)
    ratio=bool(re.search(r'\b(?:ratio|proportion|fraction|how many times)\b',q))
    if ratio and meta['unit'] is None:meta.update(unit='ratio',scale=None,currency=None)
    target_count=q.startswith('how many ') and not re.search(r'\b(?:times|percentage|ratio)\b',q)
    price_like=not target_count and bool(re.search(r'\bprice\b',q))
    per_share=not target_count and bool(re.search(r'\bper[- ](?:common |ordinary |diluted )?share\b|\bshare price\b',q) or price_like and re.search(r'\b(?:stock|shares?|warrants?)\b',q))
    physical=bool(re.search(r'\b(?:shares|years|months|days|employees|square feet|barrels|countries|facilities)\b',q))
    if per_share and meta['unit'] not in {'ratio','percentage'}:
        meta.update(unit='currency/share',scale=None)
    rate_like=bool(re.search(r'\b(?:margin|interest rate|tax rate|yield|return on|rate of|growth rate)\b',q))
    if meta['unit'] not in {'ratio','percentage','currency/share'} and not physical and not rate_like and not price_like:
        source=reporting_meta(sample.get('context',''))
        # A unique source reporting declaration supersedes a contradictory
        # dataset scale annotation. Both original annotations remain untouched.
        if not explicit and source['scale']:meta['scale']=source['scale']
        if not meta['currency'] and source['currency']:meta['currency']=source['currency']
    if meta['unit'] not in {'ratio','percentage'} and (not physical or per_share) and not rate_like:
        for marker,code in CURRENCIES.items():
            if marker in {'$','£','€','us$','usd','gbp','eur','cny','rmb'} and re.search(re.escape(marker),q,re.I):
                meta['currency']=meta['currency'] or code
    return meta
