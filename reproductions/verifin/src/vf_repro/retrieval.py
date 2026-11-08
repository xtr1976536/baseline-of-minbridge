"""Equation (1): cosine + lambda lexical label matching, then cross-encoder."""
from __future__ import annotations
from dataclasses import asdict,replace
import json
from pathlib import Path
import re
import numpy as np
from verifiqa.types import EvidenceChunk
from verifiqa.retrieval.planner import _PROMPT, retrieval_plan_from_text
from verifiqa.generation.llm_client import ChatMessage
from .common import fingerprint

def table_header(text):
    lines=[]
    for line in text.splitlines()[:28]:
        t=re.sub(r'\s+',' ',line.strip())
        if not t or re.search('table of contents',t,re.I):continue
        date_header=re.sub(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b','',t,flags=re.I)
        is_dates=bool(re.search(r'(?:19|20)\d{2}',t) and re.fullmatch(r'[\d\s,()/\-]+',date_header))
        if re.search(r'in (?:millions|thousands|billions)|except per share|year(?:s)? ended|as of|\bCONSOLIDATED\b|\bBALANCE SHEETS?\b|\bSTATEMENTS? OF\b',t,re.I) or is_dates or re.fullmatch(r'(?:20\d{2}|19\d{2}|\s|[(),$])+',t):
            lines.append(t)
    return '\n'.join(lines[:8])


def statement_scope(text,statement):
    """Prefer the requested primary statement over notes/parent-only schedules."""
    head=text[:1500].lower()
    if re.search(r'schedule i\b|financial information of parent|parent.company.only',head):return -1
    s=statement.lower()
    kind=('cash' if 'cash' in s else 'balance' if re.search(r'balance|financial position',s) else 'income' if re.search(r'income|p&l|operations',s) else '')
    if not kind:return 0
    pattern={'cash':r'statements? of cash flows','balance':r'balance sheets?|statements? of financial position',
             'income':r'statements? of (?:income|operations|earnings)'}[kind]
    for line in text.splitlines()[:14]:
        t=re.sub(r'\s+',' ',line.strip()).lower()
        if len(t)<150 and re.fullmatch(r'(?:consolidated )?(?:'+pattern+r')',t):
            return 2 if t.startswith('consolidated') else 1
    return 0


def table_labels(text):
    labels=[]
    for line in text.splitlines():
        m=re.match(r'^\s*(.+?)\s{2,}(?=[$€£(\-\d—])',line)
        if m and re.search('[A-Za-z]',m[1]):labels.append(m[1].strip())
    return labels


def row_lexical_score(labels,text):
    from .grounding import tokens
    best=0.0
    for row in table_labels(text):
        rt=tokens(row)
        for label in labels:
            lt=tokens(label)
            if lt and lt<=rt:best=max(best,len(lt)/len(rt))
    return best


def chunks_from_pages(doc_name, pages, *, words=200, overlap=40,table_aware=False):
    chunks = []
    for page in pages:
        text = page['text']
        header = table_header(text) if table_aware else '\n'.join(text.splitlines()[:4])
        lines, bucket, n = text.splitlines(), [], 0
        for line in lines:
            count = len(line.split())
            if bucket and n+count > words:
                body = '\n'.join(bucket)
                chunks.append(EvidenceChunk(chunk_id=f'{doc_name}:p{page["page"]}:c{len(chunks)}', doc_name=doc_name,page=page['page'],text=header+'\n'+body))
                retained, seen = [], 0
                for old in reversed(bucket):
                    if seen+len(old.split()) > overlap: break
                    retained.insert(0,old); seen += len(old.split())
                bucket, n = retained, seen
            bucket.append(line); n += count
        if bucket:
            chunks.append(EvidenceChunk(chunk_id=f'{doc_name}:p{page["page"]}:c{len(chunks)}',doc_name=doc_name,page=page['page'],text=header+'\n'+'\n'.join(bucket)))
    return chunks

def plan_retrieval(question, client,*,expand=False):
    # Only the question is supplied, not gold evidence, labels, or candidate claims.
    plan=retrieval_plan_from_text(client.chat([ChatMessage(role='user',content=_PROMPT.format(question=question))],stage='retrieval_plan'))
    if not expand:return plan
    from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as registry
    from verifiqa.agent.types import RoleSpec
    from .semantics import role_concept,field,undecorated,question_years
    facts=[];seen=set()
    for fact in plan.facts:
        policy=registry.find_policy(fact.name)
        variables=sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',policy.formula_templates[0]))) if policy and len(policy.formula_templates)==1 else []
        primitives=variables if len(variables)>1 else [fact.name]
        for name in primitives:
            role=RoleSpec(name,[] if len(variables)>1 else fact.aliases,fact.period)
            c=role_concept(role);aliases=list(dict.fromkeys([*role.aliases,*field(c,'aliases',[])])) if c else role.aliases
            if 'cash' in fact.statement.lower() and re.search(r'dividend',name,re.I):aliases=list(dict.fromkeys([*aliases,'dividends']))
            period=fact.period;years=question_years(question)
            if re.search(r'_(?:start|beginning|prior)$',name) and years:period=years[0]
            elif re.search(r'_(?:end|ending)$',name) and years:period=years[-1]
            key=(name,period)
            if key not in seen:facts.append(replace(fact,name=name,aliases=aliases,period=period));seen.add(key)
    return replace(plan,facts=facts or plan.facts)


def select_chunks(rankings, exact_rows, top_k, *, preserve_operand_rows=False):
    """Bounded operand coverage, using cross-encoder order within exact rows."""
    if type(top_k) is not int or top_k<1:raise ValueError('top_k_must_be_positive_integer')
    selected=[]
    if preserve_operand_rows:
        for ranked, rows in zip(rankings,exact_rows):
            # A row must match a question-derived operand label exactly. Do not
            # promote prose or choose rows using extracted/candidate values.
            best=next((i for i in ranked if i in rows),None)
            if best is not None and best not in selected:selected.append(best)
            if len(selected)==top_k:return selected
    for depth in range(max(map(len,rankings),default=0)):
        for ranked in rankings:
            if depth<len(ranked) and ranked[depth] not in selected:
                selected.append(ranked[depth])
                if len(selected)==top_k:return selected
    return selected

class Retriever:
    def __init__(self, config, cache, encoder=None, reranker=None):
        self.config, self.cache = config, Path(cache)
        if config.get('preserve_operand_rows') and not config.get('table_row_lexical'):
            raise ValueError('operand_row_preservation_requires_table_row_lexical')
        if encoder is None:
            from sentence_transformers import SentenceTransformer
            encoder = SentenceTransformer(config['embedding_model'], revision=config['embedding_revision'])
        if reranker is None:
            from sentence_transformers import CrossEncoder
            reranker = CrossEncoder(config['reranker_model'], revision=config['reranker_revision'])
        self.encoder, self.reranker = encoder, reranker

    def retrieve(self, question, plan, chunks, doc_name):
        c = self.config
        chunks = [x for x in chunks if x.doc_name == doc_name]
        if not chunks: return [], []
        key = fingerprint({'chunks':[asdict(x) for x in chunks], 'model':c['embedding_model'], 'revision':c['embedding_revision']})
        path = self.cache/(key+'.npy')
        if path.exists(): embeddings = np.load(path, allow_pickle=False)
        else:
            embeddings = np.asarray(self.encoder.encode([x.text for x in chunks],normalize_embeddings=True),dtype=np.float32)
            path.parent.mkdir(parents=True,exist_ok=True); np.save(path,embeddings)
        if embeddings.ndim!=2 or len(embeddings)!=len(chunks) or not np.isfinite(embeddings).all():
            raise ValueError('invalid_embedding_cache')
        facts = plan.facts or [None]
        rankings, exact_rows, traces = [], [], []
        for fact in facts:
            labels = [fact.name.replace('_',' '), *fact.aliases] if fact else []
            query = ' '.join([question, *(labels[:1]), fact.period if fact else '', fact.statement if fact else ''])
            prefix = 'Represent this sentence for searching relevant passages: ' if 'bge' in c['embedding_model'].lower() else ''
            vector = self.encoder.encode([prefix+query],normalize_embeddings=True)[0]
            cosine = embeddings@vector
            lex = np.array([row_lexical_score(labels,chunk.text) if c.get('table_row_lexical') else max([float(label.casefold() in chunk.text.casefold()) for label in labels if label] or [0]) for chunk in chunks])
            scores = cosine+c['lexical_weight']*lex
            first = sorted(range(len(chunks)), key=lambda i:(-scores[i], chunks[i].chunk_id))[:c['first_stage_k']]
            scope=np.array([statement_scope(x.text,fact.statement if fact else '') for x in chunks]) if c.get('primary_statements') else np.zeros(len(chunks))
            primary=[i for i in range(len(chunks)) if scope[i]==max(scope) and scope[i]>0]
            if primary:
                # Reserve a small candidate quota for primary statement rows;
                # all are still scored by Eq.(1) and the same cross encoder.
                primary=sorted(primary,key=lambda i:(-scores[i],chunks[i].chunk_id))[:4]
                first=list(dict.fromkeys([*primary,*first]))[:c['first_stage_k']]
            cross = np.asarray(self.reranker.predict([(query,chunks[i].text) for i in first])).reshape(-1)
            if len(cross)!=len(first) or not np.isfinite(cross).all():raise ValueError('invalid_reranker_response')
            ranked = [i for _, i in sorted(zip(cross,first),key=lambda p:(-p[0],chunks[p[1]].chunk_id))]
            rankings.append(ranked)
            preferred=[i for i in first if scope[i]>0 and lex[i]>0]
            if preferred:
                best_scope=max(scope[i] for i in preferred);best_lex=max(lex[i] for i in preferred if scope[i]==best_scope)
                exact_rows.append({i for i in preferred if scope[i]==best_scope and lex[i]==best_lex})
            else:exact_rows.append({i for i in first if lex[i]>=.999999})
            traces.append({'query':query,'document':doc_name,'first_stage':[{'id':chunks[i].chunk_id,'cosine':float(cosine[i]),'lexical':float(lex[i]),'score':float(scores[i]),'statement_scope':float(scope[i])} for i in first],
                           'reranked':[chunks[i].chunk_id for i in ranked]})
        selected=select_chunks(rankings,exact_rows,c['top_k'],preserve_operand_rows=c.get('preserve_operand_rows',False))
        if traces:
            traces[0]['selection']={'method':'operand_rows_then_round_robin' if c.get('preserve_operand_rows') else 'round_robin',
                                    'ids':[chunks[i].chunk_id for i in selected]}
        return [chunks[i] for i in selected], traces
