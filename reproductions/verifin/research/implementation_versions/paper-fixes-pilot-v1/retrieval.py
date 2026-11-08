"""Equation (1): cosine + lambda lexical label matching, then cross-encoder."""
from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
import re
import numpy as np
from verifiqa.types import EvidenceChunk
from verifiqa.retrieval.planner import _PROMPT, retrieval_plan_from_text
from verifiqa.generation.llm_client import ChatMessage
from .common import fingerprint

def chunks_from_pages(doc_name, pages, *, words=200, overlap=40):
    chunks = []
    for page in pages:
        text = page['text']
        header = '\n'.join(text.splitlines()[:4])
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

def plan_retrieval(question, client):
    # Only the question is supplied, not gold evidence, labels, or candidate claims.
    return retrieval_plan_from_text(client.chat([ChatMessage(role='user',content=_PROMPT.format(question=question))],stage='retrieval_plan'))

class Retriever:
    def __init__(self, config, cache, encoder=None, reranker=None):
        self.config, self.cache = config, Path(cache)
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
        rankings, traces = [], []
        for fact in facts:
            labels = [fact.name.replace('_',' '), *fact.aliases] if fact else []
            query = ' '.join([question, *(labels[:1]), fact.period if fact else '', fact.statement if fact else ''])
            prefix = 'Represent this sentence for searching relevant passages: ' if 'bge' in c['embedding_model'].lower() else ''
            vector = self.encoder.encode([prefix+query],normalize_embeddings=True)[0]
            cosine = embeddings@vector
            lex = np.array([max([float(label.casefold() in chunk.text.casefold()) for label in labels if label] or [0]) for chunk in chunks])
            scores = cosine+c['lexical_weight']*lex
            first = sorted(range(len(chunks)), key=lambda i:(-scores[i], chunks[i].chunk_id))[:c['first_stage_k']]
            cross = np.asarray(self.reranker.predict([(query,chunks[i].text) for i in first])).reshape(-1)
            if len(cross)!=len(first) or not np.isfinite(cross).all():raise ValueError('invalid_reranker_response')
            ranked = [i for _, i in sorted(zip(cross,first),key=lambda p:(-p[0],chunks[p[1]].chunk_id))]
            rankings.append(ranked)
            traces.append({'query':query,'document':doc_name,'first_stage':[{'id':chunks[i].chunk_id,'cosine':float(cosine[i]),'lexical':float(lex[i]),'score':float(scores[i])} for i in first],
                           'reranked':[chunks[i].chunk_id for i in ranked]})
        selected = []
        # Bounded round-robin permits coverage of each operand query.
        for depth in range(max(map(len, rankings))):
            for ranked in rankings:
                if depth < len(ranked) and ranked[depth] not in selected:
                    selected.append(ranked[depth])
                    if len(selected) == c['top_k']: return [chunks[i] for i in selected], traces
        return [chunks[i] for i in selected], traces
