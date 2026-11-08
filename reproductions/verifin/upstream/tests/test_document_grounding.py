"""Document grounding gives the audit engine an independent source for facts that no
XBRL/table source carries: the retrieved source text itself.

The check is two-part and value-blind: the cited figure must actually occur in the
real retrieved text (provenance), and the bound value is read *out of that text*, not
taken from the LLM's asserted value. A fabricated or mis-transcribed figure fails
provenance and is left llm_only; a corroborated figure binds to the document number so
the downstream recompute compares against the source, not the LLM.
"""
import unittest
from types import SimpleNamespace

from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.document_grounding import attach_document_calculations


def _chunk(chunk_id, text):
    return SimpleNamespace(chunk_id=chunk_id, text=text)


def _fact(name, value, unit, source_quote, *, chunk_id="c0", source_scale_quote="", fact_type=""):
    return VerificationFact(
        name=name,
        value=value,
        unit=unit,
        fact_type=fact_type,
        source_quote=source_quote,
        source_scale_quote=source_scale_quote,
        chunk_id=chunk_id,
        period="",
        row_label="",
        column="",
    )


def _ir(facts):
    return VerificationIR(
        metric="m",
        formula="",
        facts={f.name: f for f in facts},
        claimed_value=0.0,
        claim_unit="USD",
        tolerance=0.0,
    )


class ProseProvenanceTests(unittest.TestCase):
    def test_corroborated_prose_fact_binds_to_document_value(self):
        # "$700 million" is in the source; the value is read from the text and expressed
        # in the fact's own unit (USD millions -> 700), not taken from fact.value.
        ir = _ir([_fact(
            "spinoff_costs", 700.0, "USD millions",
            "We expect to incur costs of approximately $700 million separating Upjohn",
            source_scale_quote="$700 million",
        )])
        attach_document_calculations(ir, [_chunk("c0", "We expect to incur costs of approximately $700 million separating Upjohn")])
        xc = ir.xbrl_calculations
        self.assertEqual(xc["status"], "ok")
        (binding,) = xc["bindings"]
        self.assertEqual(binding["source"], "source_document")
        self.assertAlmostEqual(binding["xbrl_value"], 700.0)
        self.assertEqual(binding["binding_multiplier"], 1.0)

    def test_percent_unit_keeps_magnitude(self):
        ir = _ir([_fact("pct", 90.0, "percent", "approximately 90% has been incurred")])
        attach_document_calculations(ir, [_chunk("c0", "approximately 90% has been incurred since inception")])
        (binding,) = ir.xbrl_calculations["bindings"]
        self.assertAlmostEqual(binding["xbrl_value"], 90.0)


class TableLikeProvenanceTests(unittest.TestCase):
    def test_non_contiguous_table_quote_still_grounds_on_figure(self):
        # The linearized statement has four columns; the LLM's quote pairs the row label
        # with only the column value it used. Strict substring would (wrongly) reject it;
        # figure-in-source provenance accepts it because 594,954 is really there.
        source = "interest expense, net of amounts capitalized 137,132 201,477 594,954 799,593"
        ir = _ir([_fact("interest_expense", 0.594954, "USD millions",
                        "interest expense, net of amounts capitalized 594,954")])
        attach_document_calculations(ir, [_chunk("c0", source)])
        (binding,) = ir.xbrl_calculations["bindings"]
        self.assertAlmostEqual(binding["xbrl_value"], 0.594954)


class CorroborationTests(unittest.TestCase):
    def test_fabricated_figure_not_in_source_is_not_grounded(self):
        # The cited figure does not appear in the source -> no binding (stays llm_only),
        # never silently corroborated.
        ir = _ir([_fact("revenue", 5000.0, "USD millions", "total revenue of $5,000 million")])
        attach_document_calculations(ir, [_chunk("c0", "total revenue of $4,200 million for the year")])
        xc = ir.xbrl_calculations
        self.assertEqual(xc["bindings"], [])
        self.assertIn("figure_not_in_source:revenue", xc["diagnostics"])

    def test_uncorroborated_value_is_not_grounded(self):
        # Source says 4,200; the LLM used 4,250. Bare prose carries no reliable scale, so
        # rather than risk a false catch the fact is simply left ungrounded (llm_only).
        ir = _ir([_fact("revenue", 4250.0, "USD millions", "total revenue 4,200")])
        attach_document_calculations(ir, [_chunk("c0", "total revenue 4,200 for the fiscal year")])
        self.assertEqual(ir.xbrl_calculations["bindings"], [])

    def test_scale_invariant_match_binds_to_llm_value(self):
        # 0.594954 (USD millions) and the source figure 594,954 share significant digits;
        # the fact is corroborated and bound to the LLM's own value.
        source = "interest expense, net of amounts capitalized 137,132 201,477 594,954 799,593"
        ir = _ir([_fact("interest_expense", 0.594954, "USD millions",
                        "interest expense 594,954")])
        attach_document_calculations(ir, [_chunk("c0", source)])
        (binding,) = ir.xbrl_calculations["bindings"]
        self.assertAlmostEqual(binding["xbrl_value"], 0.594954)
        self.assertEqual(binding["source"], "source_document")


class SafetyTests(unittest.TestCase):
    def test_partial_binding_falls_back_to_no_bindings(self):
        # One fact grounds, the other doesn't -> mixed evidence is rejected entirely.
        ir = _ir([
            _fact("a", 700.0, "USD millions", "costs of $700 million", source_scale_quote="$700 million"),
            _fact("b", 100.0, "USD millions", "unsupported figure $100 million", source_scale_quote="$100 million"),
        ])
        attach_document_calculations(ir, [_chunk("c0", "costs of $700 million were incurred")])
        xc = ir.xbrl_calculations
        self.assertEqual(xc["bindings"], [])
        self.assertEqual(xc["status"], "partial_document_bindings")

    def test_ambiguous_numbers_abstain(self):
        # Quote with several numbers, none matching the reported value -> can't safely
        # pick one -> no binding.
        ir = _ir([_fact("x", 999.0, "USD millions", "values were 100 and 200 and 300")])
        attach_document_calculations(ir, [_chunk("c0", "values were 100 and 200 and 300")])
        self.assertEqual(ir.xbrl_calculations["bindings"], [])

    def test_year_tokens_are_not_treated_as_figures(self):
        ir = _ir([_fact("x", 5.0, "USD millions", "in 2022 we earned 5 million", source_scale_quote="5 million")])
        attach_document_calculations(ir, [_chunk("c0", "in 2022 we earned 5 million dollars")])
        (binding,) = ir.xbrl_calculations["bindings"]
        self.assertAlmostEqual(binding["xbrl_value"], 5.0)

    def test_absence_zero_fact_ignored(self):
        ir = _ir([_fact("z", 0.0, "USD millions", "", fact_type="absence_implies_zero")])
        attach_document_calculations(ir, [_chunk("c0", "no relevant text")])
        self.assertEqual(ir.xbrl_calculations["bindings"], [])
        self.assertEqual(ir.xbrl_calculations["status"], "no_document_bindings")


if __name__ == "__main__":
    unittest.main()
