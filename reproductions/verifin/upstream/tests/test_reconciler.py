import json
import unittest

from verifiqa.reconciler.compiler import compile_reconciler_spec
from verifiqa.reconciler.context import build_reconciler_context
from verifiqa.reconciler.runner import ReconcilerRunner
from verifiqa.reconciler.spec import ReconcilerSpec, parse_reconciler_spec
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY
from verifiqa.types import FinanceBenchExample, SolverResult, VerificationFact, VerificationIR


class FakeLlm:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, messages, temperature=0.0, stage="unknown", max_tokens=None):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "stage": stage,
                "max_tokens": max_tokens,
            }
        )
        return self.response


class FakeZ3:
    def __init__(self, status="SAT"):
        self.status = status
        self.calls = []

    def run(self, smtlib, label="", debug_unsat_core=None):
        self.calls.append(
            {
                "smtlib": smtlib,
                "label": label,
                "debug_unsat_core": debug_unsat_core,
            }
        )
        return SolverResult(solver_status=self.status, smt_path=f"/tmp/{label}.smt2")


def _quick_ratio_ir() -> VerificationIR:
    facts = {
        "cash": VerificationFact("cash", 4.0, "USD millions"),
        "short_term_investments": VerificationFact("short_term_investments", 1.0, "USD millions"),
        "receivables": VerificationFact("receivables", 5.0, "USD millions"),
        "current_liabilities": VerificationFact("current_liabilities", 5.0, "USD millions"),
    }
    bindings = []
    for name, fact in facts.items():
        bindings.append(
            {
                "fact_name": name,
                "concept": f"test:{name}",
                "context_id": "FY2024",
                "context_period": {"instant": "", "start_date": "2024-01-01", "end_date": "2024-12-31"},
                "unit_measures": ["iso4217:USD"],
                "xbrl_value": fact.value,
                "xbrl_smt_value": str(fact.value),
                "binding_multiplier": 1.0,
            }
        )
    return VerificationIR(
        metric="quick_ratio",
        formula="(cash + short_term_investments + receivables) / current_liabilities",
        facts=facts,
        claimed_value=2.0,
        claim_unit="ratio",
        tolerance=0.01,
        xbrl_calculations={
            "enabled": True,
            "status": "ok",
            "source": "test_xbrl",
            "bindings": bindings,
            "constraints": [],
        },
    )


class ReconcilerTests(unittest.TestCase):
    def test_parse_rejects_extra_keys(self):
        with self.assertRaisesRegex(ValueError, "unexpected_spec_keys"):
            parse_reconciler_spec('{"fact_bindings": {}, "formula": "none", "verdict": "pass"}')

    def test_context_masks_claim_and_source_values(self):
        example = FinanceBenchExample(
            financebench_id="example_1",
            question="What was the quick ratio?",
            company="ExampleCo",
            doc_name="EX_2024_10K",
        )
        context = build_reconciler_context(example, _quick_ratio_ir(), DEFAULT_POLICY_REGISTRY)
        payload = json.dumps(context.prompt_payload, sort_keys=True)

        self.assertIn('"value": "MASKED"', payload)
        self.assertNotIn('"xbrl_value"', payload)
        self.assertNotIn('"claimed_value"', payload)
        self.assertNotIn("4.0", payload)

    def test_compile_uses_registry_formula_and_grounded_values(self):
        context = build_reconciler_context(
            FinanceBenchExample(financebench_id="example_1", question="What was the quick ratio?"),
            _quick_ratio_ir(),
            DEFAULT_POLICY_REGISTRY,
        )
        spec = ReconcilerSpec(
            fact_bindings={
                "cash": "cash",
                "short_term_investments": "short_term_investments",
                "receivables": "receivables",
                "current_liabilities": "current_liabilities",
            },
            formula="standard_quick_ratio",
            claim_scale=1,
            claim_unit="ratio",
        )

        compiled = compile_reconciler_spec(spec, context, _quick_ratio_ir(), DEFAULT_POLICY_REGISTRY)

        self.assertEqual(compiled.status, "compiled")
        self.assertEqual(compiled.formula_expression, "(cash + short_term_investments + receivables) / current_liabilities")
        self.assertIn("(assert (! (= cash 4)", compiled.smtlib)
        self.assertIn("reconciler_claim_upper", compiled.smtlib)

    def test_runner_records_solver_verdict_without_llm_values(self):
        response = json.dumps(
            {
                "fact_bindings": {
                    "cash": "cash",
                    "short_term_investments": "short_term_investments",
                    "receivables": "receivables",
                    "current_liabilities": "current_liabilities",
                },
                "formula": "standard_quick_ratio",
                "claim_scale": 1,
                "claim_unit": "ratio",
            }
        )
        llm = FakeLlm(response)
        z3 = FakeZ3("SAT")
        runner = ReconcilerRunner(llm, registry=DEFAULT_POLICY_REGISTRY, z3_runner=z3)

        result = runner.run(
            FinanceBenchExample(financebench_id="example_1", question="What was the quick ratio?"),
            _quick_ratio_ir(),
        )

        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["valid"])
        self.assertEqual(llm.calls[0]["stage"], "reconciler_spec")
        self.assertEqual(z3.calls[0]["debug_unsat_core"], True)
        prompt = llm.calls[0]["messages"][0].content
        self.assertIn('"value": "MASKED"', prompt)
        self.assertNotIn("4.0", prompt)


if __name__ == "__main__":
    unittest.main()
