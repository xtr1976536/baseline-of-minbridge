import unittest

from verifiqa.formalization.formalizer import FormalizationError
from verifiqa.pipeline import (
    CounterexampleRavPipeline,
    PipelineConfig,
    _augment_smt_with_formula_authority_failure,
)
from verifiqa.types import FinanceBenchExample, VerificationIR, VerificationSchema
from verifiqa.verification.finqa_program import resolve_finqa_program
from verifiqa.verification.smt_generator import SmtGenerator, render_ir_smt
from verifiqa.verification.xbrl_linkbase import augment_smt_with_xbrl
from verifiqa.verification.z3_runner import Z3Runner


def _schema(metric="finqa_metric", claim_unit=""):
    return VerificationSchema(
        metric=metric,
        formula="llm_formula",
        allowed_variables=[],
        required_evidence=[],
        allowed_operators=[],
        tolerance=0.005,
        unit_policy="test",
        period_policy="test",
        claim_unit=claim_unit,
        computed_unit=claim_unit,
        precision_digits=2,
        tolerance_source="test",
    )


class FinqaProgramAuthorityTests(unittest.TestCase):
    def test_program_replaces_formula_and_grounds_const_when_source_unique(self):
        example = FinanceBenchExample(
            financebench_id="finqa_example",
            question="what is the average payment volume per transaction?",
            answer="127.4",
            raw={
                "qa": {
                    "program": "divide(637, const_5)",
                    "program_re": "divide(637, const_5)",
                    "answer": "127.4",
                    "gold_inds": {"table_1": ""},
                },
                "table": [
                    ["company", "payments volume", "total transactions"],
                    ["american express", "637", "5.0"],
                ],
            },
        )
        ir = VerificationIR(
            metric="average_payment_volume_per_transaction",
            formula="(payments_volume * 1000) / total_transactions",
            facts={},
            claimed_value=127.4,
            claim_unit="USD",
            tolerance=0.005,
            computed_unit="USD",
            precision_digits=1,
        )

        resolved = resolve_finqa_program(example, ir, _schema("average_payment_volume_per_transaction", "USD"))

        self.assertEqual(resolved["status"], "applied")
        revised = resolved["verification_ir"]
        self.assertEqual(len(revised.facts), 2)
        self.assertEqual(resolved["computed_value"], 127.4)
        self.assertEqual(revised.xbrl_calculations["formula_source"], "finqa_qa_program")
        self.assertEqual({b["source"] for b in revised.xbrl_calculations["bindings"]}, {"finqa_table"})

    def test_percent_answer_presentation_scales_ratio_program_output(self):
        example = FinanceBenchExample(
            financebench_id="finqa_percent",
            question="what was the percentage cumulative total return?",
            answer="0.935",
            raw={
                "qa": {
                    "program": "subtract(193.5, const_100), divide(#0, const_100)",
                    "program_re": "divide(subtract(193.5, const_100), const_100)",
                    "answer": "93.5%",
                    "gold_inds": {"table_1": "", "table_2": ""},
                },
                "table": [
                    ["date", "citi"],
                    ["31-dec-2012", "100.0"],
                    ["31-dec-2017", "193.5"],
                ],
            },
        )
        ir = VerificationIR(
            metric="percentage_cumulative_total_return",
            formula="llm_formula",
            facts={},
            claimed_value=93.5,
            claim_unit="percent",
            tolerance=0.05,
            computed_unit="percent",
            precision_digits=1,
        )

        resolved = resolve_finqa_program(example, ir, _schema("percentage_cumulative_total_return", "percent"))

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["raw_computed_value"], 0.935)
        self.assertEqual(resolved["output_scale"], 100.0)
        self.assertEqual(resolved["computed_value"], 93.5)


    def test_question_365_day_constant_is_grounded_from_question(self):
        example = FinanceBenchExample(
            financebench_id="finqa_day_year",
            question="based on a 365 day year, what was total annual revenue?",
            answer="3650",
            raw={
                "qa": {
                    "program": "multiply(365, 10)",
                    "program_re": "multiply(365, 10)",
                    "answer": "3650",
                    "gold_inds": {"table_1": ""},
                },
                "table": [
                    ["metric", "amount"],
                    ["daily revenue", "10"],
                ],
            },
        )
        ir = VerificationIR(
            metric="annualized_revenue",
            formula="llm_formula",
            facts={},
            claimed_value=3650.0,
            claim_unit="USD",
            tolerance=0.005,
            computed_unit="USD",
            precision_digits=0,
        )

        resolved = resolve_finqa_program(example, ir, _schema("annualized_revenue", "USD"))

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["computed_value"], 3650.0)
        bindings = resolved["verification_ir"].xbrl_calculations["bindings"]
        self.assertIn("finqa_question", {binding["source"] for binding in bindings})
        self.assertIn("finqa_table", {binding["source"] for binding in bindings})

    def test_finqa_program_bypasses_financebench_question_filter(self):
        class ScalarAnswerer:
            def generate(self, question, evidence_chunks):
                return "2057"

        class NonScalarFormalizer:
            def formalize(self, question, evidence_chunks, answer):
                raise FormalizationError("claimed_value_must_be_number")

        example = FinanceBenchExample(
            financebench_id="finqa_MRO/2007/page_149.pdf-2",
            question="if current development costs increased in 2008 as much as in 2007 , what would the 2008 total be , in millions?",
            answer="2057.0",
            evidence=[
                {
                    "evidence_text": "( in millions ) the development costs incurred during the period of 2007 is 1654 ; the development costs incurred during the period of 2006 is 1251 ; the development costs incurred during the period of 2005 is 1030 ;",
                    "doc_name": "MRO_2007_10K",
                    "source_label": "table_4",
                }
            ],
            raw={
                "qa": {
                    "program": "subtract(1654, 1251), add(#0, 1654)",
                    "program_re": "add(subtract(1654, 1251), 1654)",
                    "answer": "2057",
                    "gold_inds": {"table_4": ""},
                },
                "table": [
                    ["( in millions )", "2007", "2006", "2005"],
                    ["development costs incurred during the period", "1654", "1251", "1030"],
                ],
            },
        )
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=object(),
            answer_generator=ScalarAnswerer(),
            formalizer=NonScalarFormalizer(),
            smt_generator=SmtGenerator(None),
            config=PipelineConfig(oracle_retrieval=True, allow_sat_repair=False),
        )

        result = pipeline.run_example(example)

        self.assertEqual(result.final_status, "VERIFIED")
        self.assertEqual(result.grounding, "finqa_table_grounded")
        self.assertEqual(result.verification_checks["formula_authority"]["source"], "finqa_qa_program")
        self.assertEqual(result.first_pass_solver_status, "SAT")

    def test_pipeline_falls_back_to_finqa_program_when_formalizer_cannot_scalarize(self):
        class TwoValueAnswerer:
            def generate(self, question, evidence_chunks):
                return "Total residential mortgages balance was $1,356 million for 2013 and $2,220 million for 2012."

        class NonScalarFormalizer:
            def formalize(self, question, evidence_chunks, answer):
                raise FormalizationError("claimed_value_must_be_number")

        example = FinanceBenchExample(
            financebench_id="finqa_PNC/2013/page_62.pdf-2",
            question="in millions what was total residential mortgages balance for 2013 and 2012?",
            answer="3576.0",
            evidence=[
                {
                    "evidence_text": "in millions: total residential mortgages | december 312013: 1356 | december 312012: 2220",
                    "doc_name": "PNC_2013_10K",
                    "source_label": "table_1",
                }
            ],
            raw={
                "qa": {
                    "program": "add(1356, 2220)",
                    "program_re": "add(1356, 2220)",
                    "answer": "3576.0",
                    "gold_inds": {"table_1": ""},
                },
                "table": [
                    ["in millions", "december 312013", "december 312012"],
                    ["total residential mortgages", "1356", "2220"],
                ],
            },
        )
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=object(),
            answer_generator=TwoValueAnswerer(),
            formalizer=NonScalarFormalizer(),
            smt_generator=SmtGenerator(None),
            config=PipelineConfig(oracle_retrieval=True, allow_sat_repair=False),
        )

        result = pipeline.run_example(example)

        self.assertEqual(result.final_status, "VIOLATED")
        self.assertEqual(result.grounding, "finqa_table_grounded")
        self.assertEqual(result.verification_checks["formula_authority"]["source"], "finqa_qa_program")
        self.assertEqual(result.verification_checks["mathematical_validity"]["solver_status"], "UNSAT")

    def test_headerless_table_first_row_can_ground_program_operand(self):
        example = FinanceBenchExample(
            financebench_id="finqa_HOLX/2015/page_98.pdf-2",
            question="what is the expected growth rate in amortization expense from 2016 to 2017?",
            answer="-3.0%",
            raw={
                "qa": {
                    "program": "subtract(365.6, 377.0), divide(#0, 377.0)",
                    "program_re": "divide(subtract(365.6, 377.0), 377.0)",
                    "answer": "-3.0%",
                    "gold_inds": {"table_1": ""},
                },
                "table": [
                    ["fiscal 2016", "$ 377.0"],
                    ["fiscal 2017", "$ 365.6"],
                    ["fiscal 2018", "$ 355.1"],
                ],
            },
        )
        ir = VerificationIR(
            metric="expected_growth_rate",
            formula="llm_formula",
            facts={},
            claimed_value=-3.0,
            claim_unit="percent",
            tolerance=0.05,
            computed_unit="percent",
            precision_digits=1,
        )

        resolved = resolve_finqa_program(example, ir, _schema("expected_growth_rate", "percent"))

        self.assertEqual(resolved["status"], "applied")
        self.assertAlmostEqual(resolved["computed_value"], -3.023872679, places=6)
        self.assertEqual(resolved["output_scale"], 100.0)
        context_ids = {binding["context_id"] for binding in resolved["verification_ir"].xbrl_calculations["bindings"]}
        self.assertTrue(any("_r0_" in context_id for context_id in context_ids))
        self.assertTrue(any("_r1_" in context_id for context_id in context_ids))

    def test_formula_authority_failure_reason_forces_unsat_with_valid_name(self):
        smt = "(set-logic QF_NRA)\n(check-sat)\n"

        augmented = _augment_smt_with_formula_authority_failure(
            smt,
            {"reason": "program_operand_not_grounded:377.0"},
        )
        solver = Z3Runner().run(augmented, label="formula_authority_failure_name_test")

        self.assertIn(
            ":named formula_authority_failed_program_operand_not_grounded_377_0",
            augmented,
        )
        self.assertEqual(solver.solver_status, "UNSAT")

    def test_rendered_smt_verifies_program_claim_against_grounded_values(self):
        example = FinanceBenchExample(
            financebench_id="finqa_example",
            question="what is the average payment volume per transaction?",
            answer="127.4",
            raw={
                "qa": {
                    "program": "divide(637, const_5)",
                    "answer": "127.4",
                    "gold_inds": {"table_1": ""},
                },
                "table": [
                    ["company", "payments volume", "total transactions"],
                    ["american express", "637", "5.0"],
                ],
            },
        )
        ir = VerificationIR(
            metric="average_payment_volume_per_transaction",
            formula="wrong",
            facts={},
            claimed_value=127.4,
            claim_unit="USD",
            tolerance=0.005,
            computed_unit="USD",
            precision_digits=1,
        )
        revised = resolve_finqa_program(
            example,
            ir,
            _schema("average_payment_volume_per_transaction", "USD"),
        )["verification_ir"]

        smt = augment_smt_with_xbrl(render_ir_smt(revised), revised)
        solver = Z3Runner().run(smt, label="finqa_program_authority_test")

        self.assertEqual(solver.solver_status, "SAT")
        self.assertIn("xbrl_bind_finqa_operand_0", smt)
        self.assertIn("xbrl_bind_finqa_operand_1", smt)


if __name__ == "__main__":
    unittest.main()
