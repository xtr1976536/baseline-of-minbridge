"""Six prompt strings copied verbatim by static AST extraction from pinned source."""
import json
from pathlib import Path
import re

from .assets import Problem

PROMPTS = json.loads(Path(__file__).with_name("prompts.json").read_text(encoding="utf-8"))
LEGACY_JUDGE = "labels-v1"
ID_JUDGE = "candidate-ids-v2"


def candidate_ids(count):
    return [f"C{i:02d}" for i in range(1, count+1)]


def judge_response_format(count):
    """Constrain only the selector's serialization, not financial relevance."""
    return {"type": "json_schema", "json_schema": {"name": "function_selection", "strict": True,
        "schema": {"type": "object", "properties": {"selected_ids": {"type": "array",
            "items": {"type": "string", "enum": candidate_ids(count)}, "maxItems": 3}},
            "required": ["selected_ids"], "additionalProperties": False}}}


def id_judge_messages(question, functions):
    # Preserve the author's relevance criteria. Only replace label serialization
    # and add explicit reference IDs so no 30-position list must be counted.
    system = PROMPTS["JUDGE_USEFUL_FUNCTIONS_SYSTEM_INPUT"]
    system = system.replace("respond with [USEFUL]", "mark it as useful for selection")
    system = system.replace("respond with [USELESS]", "exclude it from selection")
    candidates = "\n\n".join(f'<candidate id="{identifier}">\n{code}\n</candidate>'
                               for identifier, code in zip(candidate_ids(len(functions)), functions))
    user = PROMPTS["JUDGE_USEFUL_FUNCTIONS_USER_INPUT"]
    user = user.replace("output [USEFUL]", "consider its candidate ID for selection")
    user = user.replace("output [USELESS]", "exclude its candidate ID")
    user = user.replace("just the relevant outputs for each function", "only the requested JSON object")
    user = user.format(question_input=question, function_input=candidates)
    old_contract = "Output the results in the following format:\n        [USEFUL, USELESS, USELESS, ...]"
    new_contract = ("Assess all candidates using the guidelines above. Return the IDs of at most the first three "
                    "USEFUL candidates in displayed retrieval order. If fewer are useful, return fewer IDs; "
                    "if none are useful, return an empty list. Do not include USELESS candidates. "
                    "Output one JSON object with the single key selected_ids and a list of distinct existing "
                    "candidate IDs as its value. Do not output positional labels, explanations, or code fences.")
    if old_contract not in user:
        raise ValueError("Pinned judge template no longer matches the reviewed output contract")
    user = user.replace(old_contract, new_contract)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def question_input(problem: Problem):
    if problem.context:
        return f"The following question context is provided for your reference.{problem.context}\n\nQuestion: {problem.question}\n"
    return f"Question: {problem.question}\n"


def messages(stage, problem, functions=(), *, judge_protocol=LEGACY_JUDGE):
    question = question_input(problem)
    if stage == "query":
        system = PROMPTS["GENERATE_RETRIEVAL_QUERY_SYSTEM_INPUT"]
        user = PROMPTS["GENERATE_RETRIEVAL_QUERY_USER_INPUT"].format(question_input=question)
    elif stage == "judge":
        if judge_protocol == ID_JUDGE:
            return id_judge_messages(question, functions)
        if judge_protocol != LEGACY_JUDGE:
            raise ValueError("Unrecognized judge protocol")
        system = PROMPTS["JUDGE_USEFUL_FUNCTIONS_SYSTEM_INPUT"]
        user = PROMPTS["JUDGE_USEFUL_FUNCTIONS_USER_INPUT"].format(question_input=question, function_input=list(functions))
    elif stage == "pot":
        system = PROMPTS["POT_SYSTEM_INPUT"]
        knowledge = "The following are the financial functions for your reference.\n" + "\n".join(functions) + "\n" if functions else ""
        user = "\n".join([question, knowledge, PROMPTS["POT_PROGRAM_PREFIX_INPUT"]])
    else:
        raise ValueError(stage)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def select_functions(raw, candidates, *, judge_protocol=LEGACY_JUDGE):
    # Author schema, with exact count checking; malformed output never silently
    # falls back to vanilla top-3 or a second model attempt.
    text = re.sub(r"^```(?:text|json)?\s*\n?(.*?)\n?```$", r"\1", raw.strip(), flags=re.S)
    if judge_protocol == ID_JUDGE:
        def unique_object(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj:
                    raise ValueError("Duplicate selector JSON key")
                obj[key] = value
            return obj
        try:
            obj = json.loads(text, object_pairs_hook=unique_object)
        except json.JSONDecodeError as exc:
            raise ValueError("Selector did not return one valid JSON object") from exc
        if not isinstance(obj, dict) or set(obj) != {"selected_ids"}:
            raise ValueError("Selector must contain only selected_ids")
        selected = obj["selected_ids"]
        if not isinstance(selected, list) or len(selected) > 3 or any(type(x) is not str for x in selected):
            raise ValueError("Selector must return zero to three string IDs")
        if len(set(selected)) != len(selected):
            raise ValueError("Selector IDs must be distinct")
        identifiers = candidate_ids(len(candidates))
        if not set(selected) <= set(identifiers):
            raise ValueError("Selector returned an unknown candidate ID")
        # Preserve the selected set and normalize only its presentation order.
        return [candidate for identifier, candidate in zip(identifiers, candidates) if identifier in selected]
    if judge_protocol != LEGACY_JUDGE:
        raise ValueError("Unrecognized judge protocol")
    if not re.fullmatch(r"\[\s*(?:USEFUL|USELESS)(?:\s*,\s*(?:USEFUL|USELESS))*\s*\]", text):
        raise ValueError("Judge did not return the ordered USEFUL/USELESS list")
    labels = [x.strip() for x in text[1:-1].split(",")]
    if len(labels) != len(candidates):
        raise ValueError("Judge label count differs from candidate count")
    return [c for c, label in zip(candidates, labels) if label == "USEFUL"][:3]
