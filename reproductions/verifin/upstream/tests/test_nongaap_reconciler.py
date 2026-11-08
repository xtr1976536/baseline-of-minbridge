import json
import unittest

from verifiqa.types import EvidenceChunk, VerificationFact, VerificationIR
from verifiqa.verification.nongaap_reconciler import NonGaapReconciler


# Real Amcor FY2023 10-K "Components of revenue change" reconciliation (Total, 12 mo).
AMCOR_TABLE = (
    "Twelve Months Ended June 30 Total\n"
    "Net sales fiscal year 2023 14,694\n"
    "Net sales fiscal year 2022 14,544\n"
    "Reported Growth % 1\n"
    "FX % (3)\n"
    "Constant Currency Growth % 4\n"
    "Raw Material Pass Through % 5\n"
    "Items affecting comparability % (1)\n"
    "Comparable Constant Currency Growth % 0\n"
)


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def chat(self, messages, temperature=0.0, stage="unknown", max_tokens=None, output_config=None):
        return json.dumps(self.payload)


def _amcor_ir(formula="constant_currency_growth_percent - raw_material_pass_through_percent - items_affecting_comparability_percent"):
    facts = {
        "constant_currency_growth_percent": VerificationFact("constant_currency_growth_percent", 4.0, "percent"),
        "raw_material_pass_through_percent": VerificationFact("raw_material_pass_through_percent", 5.0, "percent"),
        "items_affecting_comparability_percent": VerificationFact("items_affecting_comparability_percent", -1.0, "percent"),
    }
    return VerificationIR(
        metric="comparable_constant_currency_growth_percent",
        formula=formula,
        facts=facts,
        claimed_value=0.0,
        claim_unit="percent",
        tolerance=0.5,
    )


def _chunks():
    return [EvidenceChunk(chunk_id="amcor:0", doc_name="AMCOR_2023_10K", page=40, text=AMCOR_TABLE)]


class NonGaapReconcilerTests(unittest.TestCase):
    def test_authorizes_formula_that_reconciles_to_published_total(self):
        llm = FakeLLM({
            "found": True, "value": 0,
            "source_quote": "Comparable Constant Currency Growth % 0", "chunk_id": "amcor:0",
        })
        doc = NonGaapReconciler(llm).resolve(_amcor_ir(), "Real change in Sales for Amcor", _chunks())
        self.assertIsNotNone(doc)
        self.assertAlmostEqual(doc["computed_value"], 0.0)
        self.assertAlmostEqual(doc["published_total"], 0.0)
        self.assertEqual(doc["chunk_id"], "amcor:0")

    def test_rejects_when_published_total_not_found(self):
        llm = FakeLLM({"found": False, "value": None, "source_quote": "", "chunk_id": ""})
        self.assertIsNone(NonGaapReconciler(llm).resolve(_amcor_ir(), "q", _chunks()))

    def test_rejects_when_formula_does_not_reconcile(self):
        # Published total says 3, but formula(facts) = 0 -> do NOT authorize.
        llm = FakeLLM({
            "found": True, "value": 3,
            "source_quote": "Comparable Constant Currency Growth % 3", "chunk_id": "amcor:0",
        })
        # value 3 must also appear in the chunk to be grounded; it doesn't here,
        # so this also exercises the grounding guard.
        self.assertIsNone(NonGaapReconciler(llm).resolve(_amcor_ir(), "q", _chunks()))

    def test_rejects_single_fact_passthrough(self):
        # A single-fact formula trivially equals its own published total -> not an
        # independent reconciliation; must NOT be authorized (the Upjohn false-accept).
        facts = {"total_expected_separation_costs": VerificationFact("total_expected_separation_costs", 700.0, "USD millions")}
        ir = VerificationIR(
            metric="upjohn_separation_total_expected_costs",
            formula="total_expected_separation_costs",
            facts=facts, claimed_value=700.0, claim_unit="USD millions", tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="pfizer:0", doc_name="PFIZER", page=0,
            text="We expect to incur costs of approximately $700 million separating Upjohn",
        )
        llm = FakeLLM({"found": True, "value": 700, "source_quote": "$700 million", "chunk_id": "pfizer:0"})
        self.assertIsNone(NonGaapReconciler(llm).resolve(ir, "Upjohn separation costs", [chunk]))

    def test_rejects_ungrounded_value(self):
        # Value not present in the chunk -> ungrounded -> reject.
        llm = FakeLLM({
            "found": True, "value": 42,
            "source_quote": "made up", "chunk_id": "amcor:0",
        })
        self.assertIsNone(NonGaapReconciler(llm).resolve(_amcor_ir(), "q", _chunks()))


if __name__ == "__main__":
    unittest.main()
