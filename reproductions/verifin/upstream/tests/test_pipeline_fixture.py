import unittest
from copy import deepcopy
from pathlib import Path

from verifiqa.dataset import load_financebench
from verifiqa.formalization.formalizer import FormalizationError
from verifiqa.pipeline import CounterexampleRavPipeline, PipelineConfig, _formula_authority_result
from verifiqa.policy.registry import load_policy_registry
from verifiqa.retrieval.evidence_retriever import EvidenceRetriever
from verifiqa.types import (
    CertificateClaim,
    CertificateFact,
    EvidenceChunk,
    FinanceBenchExample,
    RetrievalFact,
    RetrievalPlan,
    VerificationCertificate,
    VerificationFact,
    VerificationIR,
    VerificationSchema,
)

from smt_helpers import render_counterexample_smt


CERTIFICATES = {
    "fixture_quick_ratio_amd_2022": VerificationCertificate(
        claim=CertificateClaim(metric="quick_ratio", claimed_value=1.5718, unit="ratio", period="FY2022"),
        facts=[
            CertificateFact("cash", 4835.0, "USD millions", "Cash and cash equivalents were $4,835 million", "fixture_quick_ratio_amd_2022:evidence:0", period="FY2022"),
            CertificateFact("short_term_investments", 1020.0, "USD millions", "Short-term investments were $1,020 million", "fixture_quick_ratio_amd_2022:evidence:0", period="FY2022"),
            CertificateFact("receivables", 4126.0, "USD millions", "Accounts receivable were $4,126 million", "fixture_quick_ratio_amd_2022:evidence:0", period="FY2022"),
            CertificateFact("current_liabilities", 6350.0, "USD millions", "Total current liabilities were $6,350 million", "fixture_quick_ratio_amd_2022:evidence:0", period="FY2022"),
        ],
        formula="(cash + short_term_investments + receivables) / current_liabilities",
        calculation="(4835 + 1020 + 4126) / 6350 = 1.5718",
        tolerance=0.001,
    ),
    "fixture_roa_exampleco_2023": VerificationCertificate(
        claim=CertificateClaim(metric="roa", claimed_value=0.1243, unit="ratio", period="FY2023"),
        facts=[
            CertificateFact("net_income", 4165.0, "USD millions", "Net income was $4,165 million", "fixture_roa_exampleco_2023:evidence:0", period="FY2023"),
            CertificateFact("average_assets", 33500.0, "USD millions", "Average total assets were $33,500 million", "fixture_roa_exampleco_2023:evidence:0", period="FY2023"),
        ],
        formula="net_income / average_assets",
        calculation="4165 / 33500 = 0.1243",
        tolerance=0.001,
    ),
    "fixture_fcf_amd_2022": VerificationCertificate(
        claim=CertificateClaim(metric="free_cash_flow", claimed_value=5422.0, unit="USD millions", period="FY2022"),
        facts=[
            CertificateFact("cash_from_operations", 5872.0, "USD millions", "Net cash provided by operating activities was $5,872 million", "fixture_fcf_amd_2022:evidence:0", period="FY2022"),
            CertificateFact("capital_expenditures", 450.0, "USD millions", "Capital expenditures were $450 million", "fixture_fcf_amd_2022:evidence:0", period="FY2022"),
        ],
        formula="cash_from_operations - capital_expenditures",
        calculation="5872 - 450 = 5422",
        tolerance=0.001,
    ),
    "fixture_gross_margin_exampleco_2023": VerificationCertificate(
        claim=CertificateClaim(metric="gross_margin", claimed_value=0.5273, unit="ratio", period="FY2023"),
        facts=[
            CertificateFact("gross_profit", 12444.0, "USD millions", "Gross profit was $12,444 million", "fixture_gross_margin_exampleco_2023:evidence:0", period="FY2023"),
            CertificateFact("revenue", 23601.0, "USD millions", "Revenue was $23,601 million", "fixture_gross_margin_exampleco_2023:evidence:0", period="FY2023"),
        ],
        formula="gross_profit / revenue",
        calculation="12444 / 23601 = 0.5273",
        tolerance=0.001,
    ),
    "fixture_balance_identity_exampleco_2023": VerificationCertificate(
        claim=CertificateClaim(metric="balance_sheet_residual", claimed_value=0.0, unit="USD millions", period="FY2023"),
        facts=[
            CertificateFact("assets", 33500.0, "USD millions", "Total assets were $33,500 million", "fixture_balance_identity_exampleco_2023:evidence:0", period="FY2023"),
            CertificateFact("liabilities", 25000.0, "USD millions", "Total liabilities were $25,000 million", "fixture_balance_identity_exampleco_2023:evidence:0", period="FY2023"),
            CertificateFact("equity", 8500.0, "USD millions", "Stockholders' equity was $8,500 million", "fixture_balance_identity_exampleco_2023:evidence:0", period="FY2023"),
        ],
        formula="assets - liabilities - equity",
        calculation="33500 - 25000 - 8500 = 0",
        tolerance=0.001,
    ),
}


class DeterministicAnswerGenerator:
    def generate(self, question, evidence_chunks):
        certificate = CERTIFICATES[evidence_chunks[0].financebench_id]
        return f"The {certificate.claim.metric} is {certificate.claim.claimed_value}."


class WrongAnswerGenerator:
    def generate(self, question, evidence_chunks):
        certificate = CERTIFICATES[evidence_chunks[0].financebench_id]
        return f"The {certificate.claim.metric} is {certificate.claim.claimed_value + 1.0}."


class RoundedAnswerGenerator:
    def generate(self, question, evidence_chunks):
        certificate = CERTIFICATES[evidence_chunks[0].financebench_id]
        return f"The {certificate.claim.metric} is {certificate.claim.claimed_value:.2f}."


class InsufficientAnswerGenerator:
    def generate(self, question, evidence_chunks):
        return "The retrieved evidence is insufficient to calculate the requested metric."


class FixtureFormalizer:
    def formalize(self, question, evidence_chunks, answer):
        financebench_id = evidence_chunks[0].financebench_id
        return deepcopy(CERTIFICATES[financebench_id])


class WrongFormalizer(FixtureFormalizer):
    def formalize(self, question, evidence_chunks, answer):
        model = super().formalize(question, evidence_chunks, answer)
        return VerificationCertificate(
            claim=CertificateClaim(
                metric=model.claim.metric,
                claimed_value=model.claim.claimed_value + 1.0,
                unit=model.claim.unit,
                period=model.claim.period,
            ),
            facts=model.facts,
            formula=model.formula,
            calculation=model.calculation,
            tolerance=model.tolerance,
        )


class ExtraUnusedFactFormalizer(FixtureFormalizer):
    def formalize(self, question, evidence_chunks, answer):
        model = super().formalize(question, evidence_chunks, answer)
        model.facts.append(
            CertificateFact(
                "accumulated_depreciation",
                16135.0,
                "USD millions",
                "not present in retrieved evidence",
                "missing_chunk",
            )
        )
        return model


class UnverifiableFormalizer:
    def formalize(self, question, evidence_chunks, answer):
        raise FormalizationError("not_verifiable:missing numeric facts")


class BadGroundingFormalizer(FixtureFormalizer):
    def formalize(self, question, evidence_chunks, answer):
        certificate = super().formalize(question, evidence_chunks, answer)
        fact = certificate.facts[0]
        # Point the fact at a chunk that was not retrieved so grounding fails
        # without changing the fact value (keeps the SMT claim intact).
        fact.chunk_id = "chunk_does_not_exist"
        return certificate


class FixtureSmtGenerator:
    def generate(self, claim, schema):
        return render_counterexample_smt(claim, schema)


class FailingSmtGenerator:
    def generate(self, claim, schema):
        raise AssertionError("SMT generation should not run")


class AdaptiveAnswerGenerator:
    def generate(self, question, evidence_chunks):
        return "The revenue is 100."


class AdaptiveFormalizer:
    def formalize(self, question, evidence_chunks, answer):
        return VerificationCertificate(
            claim=CertificateClaim(metric="revenue", claimed_value=100.0, unit="USD millions", period="FY2020"),
            facts=[
                CertificateFact(
                    "revenue",
                    100.0,
                    "USD millions",
                    "Revenue was $100 million",
                    "expanded:evidence:0",
                    period="FY2020",
                )
            ],
            formula="revenue",
            calculation="revenue = 100",
            tolerance=0.01,
        )

    def repair(self, certificate, error, evidence_chunks):
        return certificate


class AdaptivePlanner:
    def plan(self, question):
        return RetrievalPlan(
            metric="revenue",
            facts=[
                RetrievalFact(
                    "revenue",
                    aliases=["Revenue"],
                    period="2020",
                    statement="income statement",
                )
            ],
        )


class AdaptiveRetriever:
    def __init__(self):
        self.initial = EvidenceChunk(
            chunk_id="initial:evidence:0",
            doc_name="Target_10K",
            page=1,
            text="General annual report discussion.",
        )
        self.expanded = EvidenceChunk(
            chunk_id="expanded:evidence:0",
            doc_name="Target_10K",
            page=2,
            text="Revenue was $100 million",
        )
        self.target_facts = []

    def has_document(self, doc_name):
        return True

    def retrieve_with_plan(self, question, plan, company="", doc_name="", top_k=5, financebench_id=""):
        return [self.initial]

    def expand_for_facts(
        self,
        question,
        plan,
        target_facts,
        existing_chunks,
        company="",
        doc_name="",
        top_k=5,
        financebench_id="",
    ):
        self.target_facts = list(target_facts)
        return [self.expanded]


class AbsenceAdaptiveAnswerGenerator:
    def generate(self, question, evidence_chunks):
        return "The restructuring costs are 0."


class AbsenceAdaptiveFormalizer:
    def formalize(self, question, evidence_chunks, answer):
        expanded = any(chunk.chunk_id == "expanded:absence:0" for chunk in evidence_chunks)
        if expanded:
            chunk_id = "expanded:absence:0"
            source_quote = "There were no such costs in 2020, 2021 or 2022."
        else:
            chunk_id = "initial:absence:0"
            source_quote = (
                "The retained investment was recognized as a financial asset with zero fair value, "
                "utilizing a restructuring model of cash flows."
            )
        return VerificationCertificate(
            claim=CertificateClaim(
                metric="restructuring_costs",
                claimed_value=0.0,
                unit="USD millions",
                period="2022",
            ),
            facts=[
                CertificateFact(
                    "restructuring_costs",
                    0.0,
                    "USD millions",
                    source_quote,
                    chunk_id,
                    period="2022",
                    fact_type="absence_implies_zero",
                    raw_unit="USD",
                    source_scale="ones",
                    absence_scope={
                        "metric": "restructuring costs",
                        "period": "2022",
                        "statement": "income statement",
                    },
                )
            ],
            formula="restructuring_costs",
            calculation="0",
            tolerance=0.5,
        )

    def repair(self, certificate, error, evidence_chunks):
        return certificate


class AbsenceAdaptivePlanner:
    def plan(self, question):
        return RetrievalPlan(
            metric="restructuring_costs",
            facts=[
                RetrievalFact(
                    "restructuring_costs",
                    aliases=["restructuring costs", "restructuring charges"],
                    period="2022",
                    statement="income statement",
                )
            ],
        )


class AbsenceAdaptiveRetriever:
    def __init__(self):
        self.initial = EvidenceChunk(
            chunk_id="initial:absence:0",
            doc_name="AES_2022_10K",
            page=192,
            text=(
                "The retained investment was recognized as a financial asset with zero fair value, "
                "utilizing a restructuring model of cash flows."
            ),
        )
        self.expanded = EvidenceChunk(
            chunk_id="expanded:absence:0",
            doc_name="AES_2022_10K",
            page=95,
            text=(
                "Costs directly associated with a major restructuring program were removed "
                "from the non-GAAP definitions. There were no such costs in 2020, 2021 or 2022."
            ),
        )
        self.target_facts = []

    def has_document(self, doc_name):
        return True

    def retrieve_with_plan(self, question, plan, company="", doc_name="", top_k=5, financebench_id=""):
        return [self.initial]

    def expand_for_facts(
        self,
        question,
        plan,
        target_facts,
        existing_chunks,
        company="",
        doc_name="",
        top_k=5,
        financebench_id="",
    ):
        self.target_facts = list(target_facts)
        return [self.expanded]


def make_pipeline(
    chunks,
    formalizer=None,
    answer_generator=None,
    top_k=5,
    numeric_only=True,
    evidence_callback=None,
    policy_semantic_check=False,
):
    return CounterexampleRavPipeline(
        evidence_retriever=EvidenceRetriever(chunks),
        answer_generator=answer_generator or DeterministicAnswerGenerator(),
        formalizer=formalizer or FixtureFormalizer(),
        smt_generator=FixtureSmtGenerator(),
        config=PipelineConfig(
            evidence_top_k=top_k,
            numeric_only=numeric_only,
            oracle_retrieval=True,
            policy_semantic_check=policy_semantic_check,
        ),
        evidence_callback=evidence_callback,
    )


class PipelineFixtureTests(unittest.TestCase):
    def test_formula_authority_policy_resolution_precedes_monetary_ratio_unit_guard(self):
        example = FinanceBenchExample(
            financebench_id="financebench_id_01490",
            question=(
                "What is the amount of the gain accruing to JnJ as a result of the "
                "separation of its Consumer Health business segment, as of August 30, 2023?"
            ),
            answer="$20 billion",
        )
        ir = VerificationIR(
            metric="consumer_health_separation_gain",
            formula="separation_gain",
            facts={
                "separation_gain": VerificationFact(
                    name="separation_gain",
                    value=20000.0,
                    unit="USD millions",
                    source_quote="gain of approximately $20 billion from the separation",
                )
            },
            claimed_value=20.0,
            claim_unit="ratio",
            tolerance=0.5,
        )
        schema = VerificationSchema(
            metric=ir.metric,
            formula=ir.formula,
            allowed_variables=["separation_gain"],
            required_evidence=[],
            allowed_operators=["/"],
            tolerance=0.5,
            unit_policy="",
            period_policy="",
            claim_unit="ratio",
        )

        result = _formula_authority_result(example, ir, schema, load_policy_registry())

        self.assertTrue(result["valid"])
        self.assertEqual(
            result["check"]["policy_id"],
            "financebench_consumer_health_separation_gain",
        )
        self.assertEqual(result["verification_ir"].claim_unit, "USD billions")
        self.assertEqual(result["verification_ir"].computed_unit, "USD billions")

    def test_fixture_runs_end_to_end(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(chunks, top_k=3)
        result = pipeline.run_example(examples[0])
        self.assertTrue(result.verified)
        self.assertEqual(result.first_pass_solver_status, "SAT")
        self.assertFalse(result.abstained)
        self.assertEqual(result.verification_checks["mathematical_validity"]["status"], "passed")
        self.assertEqual(result.verification_checks["semantic_validity"]["status"], "skipped")
        self.assertEqual(result.verification_checks["policy_alignment"]["status"], "skipped")
        self.assertEqual(result.verifier_certificate["certificate_type"], "verifiqa_verifier_certificate")
        self.assertTrue(result.verifier_certificate["decision"]["verified"])
        self.assertEqual(result.verifier_certificate["smt"]["solver_status"], "SAT")
        self.assertGreaterEqual(len(result.verifier_certificate["evidence_bindings"]), 1)

    def test_policy_semantic_check_records_all_three_passed_checks(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(chunks, top_k=3, policy_semantic_check=True)
        result = pipeline.run_example(examples[0])

        self.assertTrue(result.verified)
        self.assertEqual(result.verification_checks["mathematical_validity"]["status"], "passed")
        self.assertEqual(result.verification_checks["semantic_validity"]["status"], "passed")
        self.assertEqual(result.verification_checks["policy_alignment"]["status"], "passed")
        self.assertIn("(set-logic QF_NRA)", result.smtlib)
        self.assertNotIn("verifiqa unified verification checks", result.smtlib)
        self.assertEqual(
            result.verification_checks["policy_alignment"]["policy_id"],
            "standard_quick_ratio",
        )

    def test_records_retrieved_evidence_before_answer_generation(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        records = []
        pipeline = make_pipeline(
            chunks,
            top_k=3,
            evidence_callback=lambda example, plan, evidence, status: records.append(
                (example, plan, evidence, status)
            ),
        )

        result = pipeline.run_example(examples[0])

        self.assertTrue(result.verified)
        self.assertEqual(len(records), 1)
        example, retrieval_plan, evidence_chunks, status = records[0]
        self.assertEqual(example.financebench_id, examples[0].financebench_id)
        self.assertIsNone(retrieval_plan)
        self.assertEqual(status, "retrieved")
        self.assertEqual([chunk.chunk_id for chunk in evidence_chunks], result.retrieved_chunk_ids)
        self.assertGreater(len(evidence_chunks[0].text), 0)

    def test_unused_formalizer_facts_are_pruned_before_validation(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(
            chunks,
            formalizer=ExtraUnusedFactFormalizer(),
            top_k=3,
        )

        result = pipeline.run_example(examples[0])

        self.assertTrue(result.verified)
        self.assertFalse(result.abstained)
        self.assertNotIn("accumulated_depreciation", result.claim.variables)
        self.assertNotIn("accumulated_depreciation", result.verification_ir.facts)

    def test_sat_counterexample_produces_violated(self):
        # WrongFormalizer adds +1.0 to the claimed value — a genuine violation.
        # With SAT=verified encoding, a wrong claim produces UNSAT (claim assertions
        # are inconsistent with the evidence+formula). No LLM repair available in mock,
        # so the pipeline falls through to VIOLATED.
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(
            chunks,
            formalizer=WrongFormalizer(),
            answer_generator=WrongAnswerGenerator(),
            top_k=3,
        )
        result = pipeline.run_example(examples[0])
        self.assertFalse(result.verified)
        self.assertFalse(result.abstained)
        self.assertEqual(result.final_status, "VIOLATED")
        self.assertEqual(result.first_pass_solver_status, "UNSAT")

    def test_sat_wrong_claim_produces_violated(self):
        # Same scenario with a precision-specified question.
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(
            chunks,
            formalizer=WrongFormalizer(),
            answer_generator=WrongAnswerGenerator(),
            top_k=3,
            numeric_only=False,
        )
        example = FinanceBenchExample(
            financebench_id="fixture_quick_ratio_amd_2022",
            question="What was AMD's FY2022 quick ratio? Round your answer to two decimal places.",
            answer="1.57",
            evidence=examples[0].evidence,
            company=examples[0].company,
            doc_name=examples[0].doc_name,
        )

        result = pipeline.run_example(example)

        self.assertEqual(result.final_status, "VIOLATED")
        self.assertFalse(result.verified)

    def test_question_precision_uses_displayed_answer_as_claim(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(
            chunks,
            answer_generator=RoundedAnswerGenerator(),
            top_k=3,
            numeric_only=False,
        )
        example = FinanceBenchExample(
            financebench_id="fixture_quick_ratio_amd_2022",
            question="What was AMD's FY2022 quick ratio? Round your answer to two decimal places.",
            answer="1.57",
            evidence=examples[0].evidence,
            company=examples[0].company,
            doc_name=examples[0].doc_name,
        )

        result = pipeline.run_example(example)

        self.assertEqual(result.final_status, "VERIFIED")
        self.assertTrue(result.verified)
        self.assertEqual(result.answer, "The quick_ratio is 1.57.")
        self.assertAlmostEqual(result.claim.claimed_value, 1.57)
        self.assertEqual(result.verification_checks["output_contract"]["status"], "passed")
        self.assertIn("claim_upper", result.smtlib)

    def test_invalid_formalization_abstains(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(chunks, formalizer=UnverifiableFormalizer(), top_k=3)
        result = pipeline.run_example(examples[0])
        self.assertFalse(result.verified)
        self.assertTrue(result.abstained)
        self.assertEqual(result.first_pass_solver_status, "INVALID")

    def test_refusal_answer_is_not_verified_by_certificate(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(
            chunks,
            answer_generator=InsufficientAnswerGenerator(),
            top_k=3,
        )

        result = pipeline.run_example(examples[0])

        self.assertFalse(result.verified)
        self.assertFalse(result.abstained)
        self.assertEqual(result.final_status, "VIOLATED")
        self.assertEqual(result.verification_checks["output_contract"]["reason"], "no_numeric_claim_in_answer")
        self.assertIn("output_contract_failed_no_numeric_claim_in_answer", result.smtlib)

    def test_invalid_certificate_grounding_continues_to_smt(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=EvidenceRetriever(chunks),
            answer_generator=DeterministicAnswerGenerator(),
            formalizer=BadGroundingFormalizer(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(evidence_top_k=3, oracle_retrieval=True),
        )
        result = pipeline.run_example(examples[0])
        self.assertTrue(result.verified)
        self.assertFalse(result.abstained)
        self.assertEqual(result.final_status, "VERIFIED")
        self.assertEqual(result.first_pass_solver_status, "SAT")
        grounding = result.verification_checks["certificate_grounding"]
        self.assertEqual(grounding["status"], "failed")
        self.assertIn("certificate_validation_failed", grounding["reason"])
        self.assertEqual(result.verification_checks["mathematical_validity"]["status"], "passed")
        self.assertEqual(result.verifier_certificate["decision"]["final_status"], "VERIFIED")

    def test_no_certificate_grounding_ablation_allows_smt(self):
        class UnknownChunkFormalizer(FixtureFormalizer):
            def formalize(self, question, evidence_chunks, answer):
                certificate = super().formalize(question, evidence_chunks, answer)
                certificate.facts[0].chunk_id = "unknown:evidence:0"
                return certificate

        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=EvidenceRetriever(chunks),
            answer_generator=DeterministicAnswerGenerator(),
            formalizer=UnknownChunkFormalizer(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(
                evidence_top_k=3,
                oracle_retrieval=True,
                certificate_grounding_check=False,
            ),
        )

        result = pipeline.run_example(examples[0])

        self.assertTrue(result.verified)
        self.assertFalse(result.abstained)
        self.assertEqual(result.final_status, "VERIFIED")
        self.assertEqual(result.first_pass_solver_status, "SAT")
        self.assertEqual(result.verification_checks["mathematical_validity"]["status"], "passed")

    def test_policy_formula_authority_failure_blocks_strong_verification(self):
        class SemanticMismatchAnswerGenerator:
            def generate(self, question, evidence_chunks):
                return "The ROA is 0.5."

        class SemanticMismatchFormalizer:
            def formalize(self, question, evidence_chunks, answer):
                return VerificationCertificate(
                    claim=CertificateClaim(metric="roa", claimed_value=0.5, unit="ratio"),
                    facts=[
                        CertificateFact("revenue", 50.0, "USD millions", "Revenue was $50 million", "semantic:evidence:0"),
                        CertificateFact(
                            "average_assets",
                            100.0,
                            "USD millions",
                            "Average total assets were $100 million",
                            "semantic:evidence:0",
                        ),
                    ],
                    formula="revenue / average_assets",
                    calculation="50 / 100 = 0.5",
                )

        example = FinanceBenchExample(
            financebench_id="semantic",
            question="What was ExampleCo's ROA?",
            answer="0.5",
            evidence=[
                {
                    "evidence_doc_name": "EXAMPLECO_2023_10K",
                    "evidence_page_num": 1,
                    "evidence_text": "Revenue was $50 million. Average total assets were $100 million.",
                }
            ],
        )
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=EvidenceRetriever([
                EvidenceChunk(
                    chunk_id="unused",
                    doc_name="EXAMPLECO_2023_10K",
                    page=1,
                    text="unused",
                )
            ]),
            answer_generator=SemanticMismatchAnswerGenerator(),
            formalizer=SemanticMismatchFormalizer(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(
                evidence_top_k=1,
                oracle_retrieval=True,
                numeric_only=False,
                policy_semantic_check=True,
            ),
        )

        result = pipeline.run_example(example)

        self.assertFalse(result.verified)
        self.assertTrue(result.abstained)
        self.assertEqual(result.final_status, "UNVERIFIED_FORMULA")
        self.assertEqual(result.first_pass_solver_status, "SAT")
        self.assertEqual(result.verification_checks["mathematical_validity"]["status"], "passed_unauthorized_formula")
        self.assertEqual(result.verification_checks["formula_authority"]["status"], "failed")
        self.assertFalse(result.verification_checks["formula_authority"].get("solver_enforced"))
        self.assertEqual(
            result.verification_checks["formula_authority"]["policy_id"],
            "standard_roa_assets",
        )
        self.assertIn("policy", result.verification_checks["formula_authority"]["reason"])
        self.assertIn("formula_authority_unresolved", result.verification_checks["mathematical_validity"]["reason"])
        self.assertNotIn("formula_authority_failed_", result.smtlib)
        self.assertEqual(result.verification_checks["semantic_validity"]["status"], "skipped")
        self.assertEqual(result.verification_checks["policy_alignment"]["status"], "skipped")

    def test_missing_formula_policy_blocks_strong_verification_even_when_smt_sat(self):
        class NoPolicyAnswerGenerator:
            def generate(self, question, evidence_chunks):
                return "The metric is 10."

        class NoPolicyFormalizer:
            def formalize(self, question, evidence_chunks, answer):
                return VerificationCertificate(
                    claim=CertificateClaim(metric="custom_metric_without_policy", claimed_value=10.0, unit="USD millions"),
                    facts=[CertificateFact("custom_input", 10.0, "USD millions", "Custom input was $10 million", "nopolicy:evidence:0")],
                    formula="custom_input",
                    calculation="10 = 10",
                )

        example = FinanceBenchExample(
            financebench_id="no_policy",
            question="What was ExampleCo's custom metric?",
            answer="10",
            evidence=[{"evidence_text": "Custom input was $10 million."}],
        )
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=EvidenceRetriever([EvidenceChunk("unused", "EXAMPLE_2023_10K", 1, "unused")]),
            answer_generator=NoPolicyAnswerGenerator(),
            formalizer=NoPolicyFormalizer(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(evidence_top_k=1, oracle_retrieval=True, numeric_only=False),
        )

        result = pipeline.run_example(example)

        self.assertFalse(result.verified)
        self.assertTrue(result.abstained)
        self.assertEqual(result.final_status, "UNVERIFIED_FORMULA")
        self.assertEqual(result.first_pass_solver_status, "SAT")
        self.assertEqual(result.verification_checks["formula_authority"]["reason"], "no_policy_for_metric")
        self.assertFalse(result.verification_checks["formula_authority"].get("solver_enforced"))
        self.assertNotIn("formula_authority_failed_no_policy_for_metric", result.smtlib)

    def test_adaptive_retrieval_recovers_unknown_certificate_chunk(self):
        retriever = AdaptiveRetriever()
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=retriever,
            answer_generator=AdaptiveAnswerGenerator(),
            formalizer=AdaptiveFormalizer(),
            retrieval_planner=AdaptivePlanner(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(
                evidence_top_k=1,
                oracle_retrieval=False,
                numeric_only=False,
                adaptive_retrieval=True,
            ),
        )
        example = FinanceBenchExample(
            financebench_id="adaptive",
            question="What was Target's FY2020 revenue?",
            answer="$100 million",
            company="Target",
            doc_name="Target_10K",
        )

        result = pipeline.run_example(example)

        self.assertTrue(result.verified)
        self.assertEqual(result.final_status, "VERIFIED")
        self.assertEqual(result.retrieved_chunk_ids, ["expanded:evidence:0"])
        self.assertEqual([fact.name for fact in retriever.target_facts], ["revenue"])

    def test_adaptive_retrieval_recovers_unsupported_absence_fact(self):
        retriever = AbsenceAdaptiveRetriever()
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=retriever,
            answer_generator=AbsenceAdaptiveAnswerGenerator(),
            formalizer=AbsenceAdaptiveFormalizer(),
            retrieval_planner=AbsenceAdaptivePlanner(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(
                evidence_top_k=1,
                oracle_retrieval=False,
                numeric_only=False,
                adaptive_retrieval=True,
            ),
        )
        example = FinanceBenchExample(
            financebench_id="adaptive_absence",
            question=(
                "What is the quantity of restructuring costs directly outlined in AES "
                "Corporation's income statements for FY2022? If restructuring costs are "
                "not explicitly outlined then state 0."
            ),
            answer="0",
            company="AES",
            doc_name="AES_2022_10K",
        )

        result = pipeline.run_example(example)

        self.assertTrue(result.verified)
        self.assertEqual(result.final_status, "VERIFIED")
        self.assertEqual(result.retrieved_chunk_ids, ["expanded:absence:0"])
        self.assertEqual([fact.name for fact in retriever.target_facts], ["restructuring_costs"])

    def test_ungrounded_absence_fact_is_solver_violation(self):
        retriever = AbsenceAdaptiveRetriever()
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=retriever,
            answer_generator=AbsenceAdaptiveAnswerGenerator(),
            formalizer=AbsenceAdaptiveFormalizer(),
            retrieval_planner=AbsenceAdaptivePlanner(),
            smt_generator=FixtureSmtGenerator(),
            config=PipelineConfig(
                evidence_top_k=1,
                oracle_retrieval=False,
                numeric_only=False,
                adaptive_retrieval=False,
            ),
        )
        example = FinanceBenchExample(
            financebench_id="unsupported_absence",
            question=(
                "What is the quantity of restructuring costs directly outlined in AES "
                "Corporation's income statements for FY2022? If restructuring costs are "
                "not explicitly outlined then state 0."
            ),
            answer="0",
            company="AES",
            doc_name="AES_2022_10K",
        )

        result = pipeline.run_example(example)

        self.assertFalse(result.verified)
        self.assertFalse(result.abstained)
        self.assertEqual(result.final_status, "VIOLATED")
        self.assertEqual(result.first_pass_solver_status, "UNSAT")
        self.assertEqual(result.verification_checks["formula_authority"]["status"], "failed")
        self.assertTrue(result.verification_checks["formula_authority"].get("solver_enforced"))
        self.assertIn("absence_fact_not_grounded", result.verification_checks["formula_authority"]["reason"])
        self.assertIn("formula_authority_failed", result.verification_checks["mathematical_validity"]["reason"])
        self.assertIn("formula_authority_failed_", result.smtlib)

    def test_non_numerical_question_abstains_before_retrieval(self):
        _, chunks = load_financebench(Path("data/fixtures"))
        pipeline = CounterexampleRavPipeline(
            evidence_retriever=EvidenceRetriever(chunks),
            answer_generator=DeterministicAnswerGenerator(),
            formalizer=FixtureFormalizer(),
            smt_generator=FailingSmtGenerator(),
            config=PipelineConfig(evidence_top_k=3),
        )
        example = FinanceBenchExample(
            financebench_id="qualitative",
            question="Is 3M a capital-intensive business based on FY2022 data?",
            answer="No. Fixed assets/Total Assets: 20%",
        )
        result = pipeline.run_example(example)
        self.assertFalse(result.verified)
        self.assertTrue(result.abstained)
        self.assertEqual(result.first_pass_solver_status, "INVALID")
        self.assertEqual(result.diagnostics.schema_or_smt_error, "non_numerical_question")

    def test_all_fixture_questions_verify(self):
        examples, chunks = load_financebench(Path("data/fixtures"))
        pipeline = make_pipeline(chunks, top_k=5, numeric_only=False)
        results = [pipeline.run_example(example) for example in examples]
        self.assertEqual(len(results), 5)
        self.assertTrue(all(result.verified for result in results), results)
        self.assertTrue(all(not result.abstained for result in results), results)


if __name__ == "__main__":
    unittest.main()
