"""Documented taxonomy variants with filing-label and period-type restrictions."""
from .grounding import tokens

RULES={
    'InventoryLike':{
        'qname':'us-gaap:InventoryFinishedGoodsNetOfReserves',
        'labels':['inventories','inventory','total inventories','inventories net'],
        'period_type':'instant',
        'restriction':'Admit as total inventory only when the issuer presents this tag as the inventory total, never a row labelled finished goods.',
        'source':'https://xbrl.us/data-rule/dqc_0015-le-V3pr/'},
    'ReceivablesLike':{
        'qname':'us-gaap:ReceivablesNetCurrent',
        'labels':['receivables','receivables net','accounts receivable net','trade receivables net'],
        'period_type':'instant',
        'restriction':'Use the net receivables balance, not gross receivables, tax assets or the cash-flow change in receivables.',
        'source':'https://xbrl.fasb.org/us-gaap/2025/'},
}


def qualified_extension(concept_id,filing):
    rule=RULES.get(concept_id)
    if not rule:return None
    allowed=[tokens(x) for x in rule['labels']]
    labels=filing.get('labels',{}).get(rule['qname'],[])
    if any(tokens(label) in allowed for label in labels):return rule
    return None
