import asyncio
import json
import re


class ScriptedClient:
    """Offline protocol simulation, not a language model or accuracy result."""
    def __init__(self, constraints, evidence=None, *, reject=(), plan=None):
        self.constraints = constraints
        self.evidence = evidence or {}
        self.reject = reject
        self.plan = plan or {"reasoning_type": "DirectRetrieval", "operator": "sum",
                             "subgoals": [{"metric": "Gross Profit", "constraints": constraints}],
                             "precision": "unknown"}
        self.calls = []
        self.active = self.max_active = 0

    async def json(self, task, prompt):
        self.calls.append((task, prompt))
        if task == "OQA":
            return self.plan
        if task == "OES":
            var = json.loads(prompt.rsplit("Variables to resolve:\n", 1)[1].split("\nReturn JSON", 1)[0])[0]
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            await asyncio.sleep(0.001)
            self.active -= 1
            key = (var["metric"], str(var["constraints"]["temporal_scope"]))
            found = self.evidence.get(key, self.evidence.get(var["metric"]))
            if found is None:
                return {"found": False, "var_bindings": {}, "missing_vars": ["v1"], "notes": "Not reported"}
            value, snippet = found
            return {"found": True, "var_bindings": {"v1": {
                "metric": var["metric"], "constraints": var["constraints"],
                "value": value, "context": snippet, "confidence": 1.0,
            }}, "missing_vars": [], "notes": None if var["metric"].casefold() in snippet.casefold()
                else f"Resolved {var['metric']} through registered alias"}
        if task == "Verify":
            paths = json.loads(prompt.rsplit("Candidate paths:\n", 1)[1])
            return {"path_decisions": [{"path_id": p["path_id"],
                "decision": "INVALID" if p["path_id"] in self.reject else "VALID",
                "justification": "Offline test decision"} for p in paths]}
        raise AssertionError(task)

    async def complete(self, task, prompt):
        self.calls.append((task, prompt))
        if task == "OPE.metric":
            rhs = re.search(r"Exact symbolic RHS: ([^\n]+)", prompt)[1]
            required = json.loads(prompt.split("Required variables: ", 1)[1].split("\nPlease generate", 1)[0])
            assignments = "\n".join(f'    {r["symbol"]} = vars[{r["key"]!r}]' for r in required)
            return f'def compute(vars):\n{assignments}\n    return {{"value": {rhs}, "trace": {{}}}}'
        if task == "OPE.final":
            values = ', '.join(f'vars["v{i+1}"]' for i in range(len(self.plan["subgoals"])))
            expression = f'sum([{values}])'
            meta = self.constraints["meta"]
            if self.plan["operator"] == "difference":
                expression = 'vars["v1"] - vars["v2"]'
            elif self.plan["operator"] == "change ratio":
                expression = '(vars["v1"] - vars["v2"]) / vars["v2"]'
                meta = {"currency": None, "scale": None, "unit": "ratio"}
            return 'def compute(vars):\n    return {"value": ' + expression + ', "trace": {"output_meta": ' + repr(meta) + '}}'
        raise AssertionError(task)
