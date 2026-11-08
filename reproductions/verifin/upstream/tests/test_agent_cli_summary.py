from types import SimpleNamespace

from verifiqa.agent.cli import _annotate_verified_correctness, _claim_answer, _result_to_dict, _summarize_rows
from verifiqa.agent.types import AgentResult
from verifiqa.types import EvidenceChunk, FinanceBenchExample


def _row(status, answer, gold):
    row = {
        "status": status,
        "answer": answer,
        "raw_answer": gold,
    }
    _annotate_verified_correctness(row)
    return row


def test_agent_performance_scores_solver_status_against_gold_expectation():
    rows = [
        _row("VERIFIED", answer="10.0", gold="10.0"),
        _row("VERIFIED", answer="12.0", gold="10.0"),
        _row("VIOLATED", answer="12.0", gold="10.0"),
        _row("VIOLATED", answer="10.0", gold="10.0"),
        _row("ABSTAIN", answer="10.0", gold="10.0"),
    ]

    summary = _summarize_rows(rows, elapsed_s=1.2)

    assert summary["verified"] == 2
    assert summary["violated"] == 2
    assert summary["verified_correct"] == 1
    assert summary["verified_incorrect"] == 1
    assert summary["violated_correct"] == 1
    assert summary["violated_incorrect"] == 1
    assert summary["all_verifications"] == 4
    assert summary["correct_verifications"] == 2
    assert summary["incorrect_verifications"] == 2
    assert summary["solver_verdicts"] == 4
    assert summary["correct_solver_verdicts"] == 2
    assert summary["incorrect_solver_verdicts"] == 2
    assert summary["expected_sat"] == 3
    assert summary["expected_unsat"] == 2
    assert summary["actual_sat"] == 2
    assert summary["actual_unsat"] == 2
    assert summary["accuracy"] == 0.5
    assert summary["solver_accuracy"] == 0.5
    assert summary["verification_precision"] == 0.5
    assert summary["violation_precision"] == 0.5
    assert summary["sat_precision"] == 0.5
    assert summary["unsat_precision"] == 0.5
    assert summary["decision_accuracy"] == 0.5
    assert summary["overall_accuracy"] == 0.4


def test_agent_verified_correct_means_sat_matches_expected_sat():
    row = _row("VERIFIED", answer="$8.70", gold="$8.70")

    assert row["answer_matches_gold"] is True
    assert row["actual_solver_status"] == "SAT"
    assert row["expected_solver_status"] == "SAT"
    assert row["solver_correct"] is True
    assert row["verified_correct"] is True
    assert row["decision_correct"] is True
    assert row["decision_correct_reason"] == "solver_status_matches_gold_expectation"


def test_agent_gold_matching_uses_claim_precision_not_five_percent_window():
    row = {
        "status": "VIOLATED",
        "solver_status": "UNSAT",
        "question": (
            "What was IBM's FY2025 income before income taxes, in USD millions? "
            "Round to the nearest million."
        ),
        "answer": "10,564",
        "raw_answer": "$10,328 million",
    }

    _annotate_verified_correctness(row)

    assert row["answer_matches_gold"] is False
    assert row["expected_solver_status"] == "UNSAT"
    assert row["solver_correct"] is True


class FakeAnswerGenerator:
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def generate(self, question, chunks, **kwargs):
        self.calls.append((question, chunks))
        return self.answer


def test_agent_claim_answer_defaults_to_generated_answer():
    example = FinanceBenchExample(
        financebench_id="fb_1",
        question="What is revenue?",
        answer="10",
    )
    chunks = [EvidenceChunk("fb_1:evidence:0", "doc", None, "Revenue was 12.")]
    generator = FakeAnswerGenerator("12")

    answer, source = _claim_answer(
        example,
        SimpleNamespace(claim_source="generated_answer"),
        answer_generator=generator,
        evidence_chunks=chunks,
    )

    assert answer == "12"
    assert source == "generated_answer"
    assert generator.calls == [("What is revenue?", chunks)]


def test_agent_result_keeps_generated_claim_separate_from_gold_answer():
    example = FinanceBenchExample(
        financebench_id="fb_1",
        question="What is revenue?",
        answer="10",
        raw={"answer": "10"},
    )
    result = AgentResult(
        question=example.question,
        answer="12",
        status="VIOLATED",
        solver_status="UNSAT",
    )

    row = _result_to_dict(
        result,
        example,
        evidence_text="Revenue was 12.",
        elapsed=0.1,
        claim_source="generated_answer",
    )

    assert row["claim_source"] == "generated_answer"
    assert row["claim_input_answer"] == "12"
    assert row["answer"] == "12"
    assert row["raw_answer"] == "10"
