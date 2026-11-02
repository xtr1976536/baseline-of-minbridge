"""ReAct-only Chat/continuation boundary adapter. Never constructs environment evidence."""
import re


def request_prefix(task, prompt):
    if task in ('hotpotqa', 'fever'):
        match=re.search(r'(Thought|Action)\s+(\d+):\s*$',prompt)
        if not match:
            raise ValueError('Missing author Thought/Action continuation suffix')
        kind,index=match.groups()
        output=(f'Output only the continuation: a brief thought followed by "Action {index}: Search[entity], Lookup[keyword], or Finish[answer]".'
                if kind=='Thought' else 'Output only one action: Search[entity], Lookup[keyword], or Finish[answer].')
        return output+' Do not repeat examples, restart numbering, or write Observation; observations come only from the environment.\n\n'
    if task=='alfworld':
        return 'Continue the final task with exactly one action line, matching the examples (including think: when needed). Do not output observations, example episodes, or future steps.\n\n'
    if task=='webshop':
        return 'Continue the final task with exactly one action: think[...], search[...], or click[...]. Do not output observations, example episodes, or future steps.\n\n'
    raise ValueError(task)


def adapt_response(task, prompt, raw, stop):
    text=raw.strip()
    text=re.sub(r'^```[^\n]*\n','',text)
    text=re.sub(r'\n```\s*$','',text)
    # Enforce requested stop boundaries locally if the relay ignores them.
    # A generated Observation is untrusted model text, never a tool result.
    limits=[]
    for token in stop if isinstance(stop,list) else [stop]:
        if token and token in text:limits.append(text.index(token))
    obs=re.search(r'\bObservation(?:\s+\d+)?\s*:',text,re.I)
    if obs:limits.append(obs.start())
    if limits:text=text[:min(limits)].rstrip()
    # Only collapse exact full-response repetition; never choose among alternatives.
    copies_removed=0
    for copies in range(4,1,-1):
        if len(text)%copies==0:
            unit=text[:len(text)//copies]
            if unit and unit*copies==text:
                text=unit.strip();copies_removed=copies-1;break
    info={'policy':'react-continuation-v1','discarded_generated_observation':bool(obs),'exact_duplicate_copies_removed':copies_removed,'changed':False}
    if task in ('hotpotqa','fever'):
        match=re.search(r'(Thought|Action)\s+(\d+):\s*$',prompt)
        if not match:raise ValueError('Missing continuation marker')
        kind,index=match.groups()
        # In action-only calls a leading current Action label is display scaffolding.
        if kind=='Action':
            text=re.sub(r'^\s*Action(?:\s+'+index+r')?:\s*','',text,flags=re.I)
            action=re.fullmatch(r'(?i)(Search|Lookup|Finish)\[([^\r\n]*)\]',text)
            if not action:raise ValueError('Invalid single action continuation')
            result=action[1].capitalize()+'['+action[2]+']'
        else:
            text=re.sub(r'^\s*Thought(?:\s+'+index+r')?:\s*','',text,flags=re.I)
            marker=re.search(r'\bAction(?:\s+(\d+))?:\s*',text,re.I)
            if not marker:
                # Let the unchanged author's webthink invoke its own action-only retry.
                result=text.split('\n')[0]
            else:
                if marker[1] and marker[1]!=index:raise ValueError('Model restarted or changed step numbering')
                thought=text[:marker.start()].strip()
                tail=text[marker.end():].strip()
                action=re.match(r'(?i)(Search|Lookup|Finish)\[([^\r\n]*?)\]',tail)
                if not action:raise ValueError('Missing supported action')
                remainder=tail[action.end():].strip()
                # Do not select one action among several generated plans.
                if remainder:raise ValueError('Unexpected text after single action')
                result=thought+'\nAction '+index+': '+action[1].capitalize()+'['+action[2]+']'
    else:
        text=re.sub(r'^\s*(?:Action|Act)(?:\s+\d+)?:\s*','',text,flags=re.I).strip()
        if task=='alfworld':text=re.sub(r'^>\s*','',text)
        if '\n' in text:raise ValueError('Expected one household/shopping action line')
        if task=='webshop' and not re.fullmatch(r'(think|search|click)\[[^\r\n]*\]',text):raise ValueError('Invalid shopping action')
        if not text:raise ValueError('Empty action')
        result=text
    info['changed']=result!=raw.strip()
    return result,info
