import verifiqa.agent.agent as agent_mod
from verifiqa.agent.agent import AgentConfig, VerificationAgent, _facts_in_core
from verifiqa.agent.types import ClaimedAnswer, ClaimSpec, GroundedFact, RoleSpec
from verifiqa.types import SolverResult


class FakeSmtGenerator:
    def __init__(self):
        self.irs = []

    def generate_ir(self, ir):
        self.irs.append(ir)
        return f"(set-logic QF_NRA)\n; smt {len(self.irs)}"


class FakeZ3:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = []

    def run(self, smtlib, label=""):
        self.calls.append((smtlib, label))
        status = self.statuses.pop(0)
        if status == "UNSAT":
            return SolverResult(
                solver_status="UNSAT",
                unsat_core=["evidence_numerator", "formula_ratio", "claim_lower"],
            )
        return SolverResult(solver_status=status)


class FakeZ3WithCore(FakeZ3):
    def __init__(self, statuses, unsat_core):
        super().__init__(statuses)
        self.unsat_core = list(unsat_core)

    def run(self, smtlib, label=""):
        self.calls.append((smtlib, label))
        status = self.statuses.pop(0)
        if status == "UNSAT":
            return SolverResult(solver_status="UNSAT", unsat_core=list(self.unsat_core))
        return SolverResult(solver_status=status)


def _patch_ratio_inputs(monkeypatch, numerator: float = 2.0, claimed: float = 2.0):
    claim_spec = ClaimSpec(
        metric="ratio",
        formula="numerator / denominator",
        roles=[
            RoleSpec(name="numerator", aliases=["numerator"], period="2022"),
            RoleSpec(name="denominator", aliases=["denominator"], period="2022"),
        ],
        claim_unit="ratio",
        tolerance=0.01,
        formula_source="document_derived",
        claimed_value=claimed,
        claimed_unit="ratio",
    )
    facts = {
        "numerator": GroundedFact("numerator", numerator, "other", f"numerator {numerator:g}"),
        "denominator": GroundedFact("denominator", 1.0, "other", "denominator 1"),
    }
    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=claimed, unit="ratio"),
    )
    monkeypatch.setattr(
        agent_mod,
        "extract_facts_parallel",
        lambda *args, **kwargs: dict(facts),
    )
    return claim_spec, facts


def test_facts_in_core_matches_named_evidence_assertions():
    facts = {
        "numerator": GroundedFact("numerator", 1.0, "other", "numerator 1"),
        "revenue_2022": GroundedFact("revenue_2022", 2.0, "other", "revenue 2"),
    }

    assert _facts_in_core(["evidence_numerator", "evidence_revenue_2022"], facts) == [
        "numerator",
        "revenue_2022",
    ]


def test_unsat_feedback_retry_tries_twice_and_uses_computed_mismatch(monkeypatch):
    claim_spec = ClaimSpec(
        metric="ratio",
        formula="numerator / denominator",
        roles=[
            RoleSpec(name="numerator", aliases=["numerator"], period="2022"),
            RoleSpec(name="denominator", aliases=["denominator"], period="2022"),
        ],
        claim_unit="ratio",
        tolerance=0.01,
        formula_source="document_derived",
        claimed_value=2.0,
        claimed_unit="ratio",
    )
    initial_facts = {
        "numerator": GroundedFact("numerator", 1.0, "other", "numerator 1"),
        "denominator": GroundedFact("denominator", 1.0, "other", "denominator 1"),
    }
    feedback_calls = []

    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=2.0, unit="ratio"),
    )
    monkeypatch.setattr(
        agent_mod,
        "extract_facts_parallel",
        lambda *args, **kwargs: dict(initial_facts),
    )

    def fake_feedback_extract(role, evidence_text, formula, llm_client, **kwargs):
        feedback_calls.append((kwargs["attempt"], role.name, kwargs["computed_value"]))
        if kwargs["attempt"] == 1:
            return None
        return GroundedFact("numerator", 2.0, "other", "numerator 2")

    monkeypatch.setattr(
        agent_mod,
        "extract_fact_with_feedback",
        fake_feedback_extract,
    )

    z3 = FakeZ3(["UNSAT", "SAT"])
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=FakeSmtGenerator(),
        z3_runner=z3,
        config=AgentConfig(max_unsat_fact_retries=2),
    )

    result = agent.run(
        "What is numerator divided by denominator?",
        "2.0",
        "numerator 1\nnumerator 2\ndenominator 1",
    )

    assert result.status == "VERIFIED"
    assert result.facts["numerator"].value == 2.0
    assert feedback_calls == [(1, "numerator", 1.0), (2, "numerator", 1.0)]
    assert len(z3.calls) == 2
    assert result.diagnostics["unsat_fact_retries"][0]["changed"] == []
    assert result.diagnostics["unsat_fact_retries"][1]["changed"] == ["numerator"]
    assert result.diagnostics["unsat_fact_retries"][1]["solver_status"] == "SAT"


def test_unsat_retry_reapplies_money_unit_normalization(monkeypatch):
    claim_spec = ClaimSpec(
        metric="total_capital_change",
        formula="total_capital_2008 - total_capital_2007",
        roles=[
            RoleSpec(name="total_capital_2007", aliases=["total capital"], period="2007"),
            RoleSpec(name="total_capital_2008", aliases=["total capital"], period="2008"),
        ],
        claim_unit="USD billions",
        tolerance=0.005,
        formula_source="document_derived",
        claimed_value=-13.2,
        claimed_unit="USD billions",
    )
    initial_facts = {
        "total_capital_2007": GroundedFact(
            "total_capital_2007",
            120.0,
            "USD billions",
            "2007 total capital 120.0",
        ),
        "total_capital_2008": GroundedFact(
            "total_capital_2008",
            108.4,
            "USD billions",
            "2008 total capital 108.4",
        ),
    }

    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=-13.2, unit="USD billions"),
    )
    monkeypatch.setattr(
        agent_mod,
        "extract_facts_parallel",
        lambda *args, **kwargs: dict(initial_facts),
    )

    def fake_feedback_extract(role, evidence_text, formula, llm_client, **kwargs):
        if role.name != "total_capital_2007":
            return None
        return GroundedFact(
            "total_capital_2007",
            121.6,
            "USD billions",
            "2007 total capital 121.6",
        )

    monkeypatch.setattr(agent_mod, "extract_fact_with_feedback", fake_feedback_extract)

    smt_generator = FakeSmtGenerator()
    z3 = FakeZ3WithCore(["UNSAT", "SAT"], ["evidence_total_capital_2007", "claim_lower"])
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=z3,
    )

    result = agent.run(
        "what was the change in billions in total capital from 2007 to 2008?",
        "-13.2 billion",
        "2007 total capital 120.0\n2007 total capital 121.6\n2008 total capital 108.4",
    )

    assert result.status == "VERIFIED"
    assert len(smt_generator.irs) == 2
    retried_ir = smt_generator.irs[1]
    assert retried_ir.facts["total_capital_2007"].value == 121600.0
    assert retried_ir.facts["total_capital_2008"].value == 108400.0
    assert retried_ir.claimed_value == -13200.0
    assert retried_ir.facts["total_capital_2007"].unit == "USD millions"


def test_smt_consensus_accepts_three_matching_sat_results(monkeypatch):
    _patch_ratio_inputs(monkeypatch, numerator=2.0, claimed=2.0)
    smt_generator = FakeSmtGenerator()
    z3 = FakeZ3(["SAT", "SAT", "SAT"])
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=z3,
        config=AgentConfig(require_smt_consensus=True),
    )

    result = agent.run(
        "What is numerator divided by denominator?",
        "2.0",
        "numerator 2\ndenominator 1",
    )

    assert result.status == "VERIFIED"
    assert len(smt_generator.irs) == 3
    assert len(z3.calls) == 3
    assert [run["solver_status"] for run in result.diagnostics["smt_consensus"]] == [
        "SAT",
        "SAT",
        "SAT",
    ]


def test_agent_uses_generic_operation_authority_formula(monkeypatch):
    claim_spec = ClaimSpec(
        metric="explicit_ratio",
        formula="denominator / numerator",
        roles=[
            RoleSpec(name="numerator", aliases=["numerator"], period=""),
            RoleSpec(name="denominator", aliases=["denominator"], period=""),
        ],
        claim_unit="ratio",
        tolerance=0.01,
        formula_source="generic_operation",
        operation="generic_ratio",
    )
    facts = {
        "numerator": GroundedFact("numerator", 2.0, "other", "numerator 2", row_label="numerator"),
        "denominator": GroundedFact(
            "denominator",
            10.0,
            "other",
            "denominator 10",
            row_label="denominator",
        ),
    }

    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=5.0, unit="ratio"),
    )
    monkeypatch.setattr(agent_mod, "extract_facts_parallel", lambda *args, **kwargs: dict(facts))

    smt_generator = FakeSmtGenerator()
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=FakeZ3(["SAT"]),
    )

    result = agent.run(
        "what was the ratio of numerator to denominator?",
        "5.0",
        "numerator 2\ndenominator 10",
    )

    assert result.status == "VERIFIED"
    assert smt_generator.irs[0].formula == "numerator / denominator"
    assert result.diagnostics["generic_operation_authority"]["operation"] == "generic_ratio"


def test_agent_rejects_unresolved_generic_formula_authority(monkeypatch):
    claim_spec = ClaimSpec(
        metric="segment_share",
        formula="segment",
        roles=[RoleSpec(name="segment", aliases=["segment"], period="")],
        claim_unit="percent",
        tolerance=0.01,
        formula_source="generic_operation",
        operation="proportion",
    )
    facts = {
        "segment": GroundedFact("segment", 60.0, "other", "segment 60", row_label="segment"),
    }

    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=60.0, unit="percent"),
    )
    monkeypatch.setattr(agent_mod, "extract_facts_parallel", lambda *args, **kwargs: dict(facts))

    smt_generator = FakeSmtGenerator()
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=FakeZ3(["SAT"]),
    )

    result = agent.run(
        "what percentage of total revenue was the segment?",
        "60%",
        "segment 60",
    )

    assert result.status == "UNVERIFIED_FORMULA"
    assert result.failure_reason == "generic_operation_authority_unresolved"
    assert smt_generator.irs == []


def test_smt_consensus_abstains_when_statuses_disagree(monkeypatch):
    _patch_ratio_inputs(monkeypatch, numerator=2.0, claimed=2.0)
    smt_generator = FakeSmtGenerator()
    z3 = FakeZ3(["SAT", "UNSAT", "SAT"])
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=z3,
        config=AgentConfig(require_smt_consensus=True),
    )

    result = agent.run(
        "What is numerator divided by denominator?",
        "2.0",
        "numerator 2\ndenominator 1",
    )

    assert result.status == "ABSTAIN"
    assert result.failure_reason == "smt_consensus_failed"
    assert len(smt_generator.irs) == 3
    assert [run["solver_status"] for run in result.diagnostics["smt_consensus"]] == [
        "SAT",
        "UNSAT",
        "SAT",
    ]


def test_smt_consensus_preserves_unsat_core_for_fact_retry(monkeypatch):
    _patch_ratio_inputs(monkeypatch, numerator=1.0, claimed=2.0)
    feedback_calls = []

    def fake_feedback_extract(role, evidence_text, formula, llm_client, **kwargs):
        feedback_calls.append((kwargs["attempt"], role.name, kwargs["computed_value"]))
        if kwargs["attempt"] == 1:
            return None
        return GroundedFact("numerator", 2.0, "other", "numerator 2")

    monkeypatch.setattr(agent_mod, "extract_fact_with_feedback", fake_feedback_extract)

    smt_generator = FakeSmtGenerator()
    z3 = FakeZ3(["UNSAT", "UNSAT", "UNSAT", "SAT", "SAT", "SAT"])
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt_generator,
        z3_runner=z3,
        config=AgentConfig(require_smt_consensus=True, max_unsat_fact_retries=2),
    )

    result = agent.run(
        "What is numerator divided by denominator?",
        "2.0",
        "numerator 1\nnumerator 2\ndenominator 1",
    )

    assert result.status == "VERIFIED"
    assert feedback_calls == [(1, "numerator", 1.0), (2, "numerator", 1.0)]
    assert len(smt_generator.irs) == 6
    assert len(z3.calls) == 6
    assert result.diagnostics["unsat_fact_retries"][1]["solver_status"] == "SAT"
    assert len(result.diagnostics["unsat_fact_retries"][1]["smt_consensus"]) == 3


def test_claimspec_consensus_abstains_before_claim_parse(monkeypatch):
    claim_spec = ClaimSpec(
        metric="revenue_change",
        formula="revenue_2022 - revenue_2021",
        roles=[
            RoleSpec(name="revenue_2021", aliases=["revenue"], period="2021"),
            RoleSpec(name="revenue_2022", aliases=["revenue"], period="2022"),
        ],
        claim_unit="USD millions",
        tolerance=0.01,
        formula_source="generic_operation",
    )
    diagnostics = {
        "claimspec_consensus": {
            "runs": [{"index": 1, "spec": {"formula": claim_spec.formula}}],
            "agreed": False,
            "failure_reason": "formula_mismatch",
        }
    }
    monkeypatch.setattr(
        agent_mod,
        "decompose_question_consensus",
        lambda *args, **kwargs: (claim_spec, diagnostics, "claimspec_consensus_failed"),
    )

    def fail_parse(*args, **kwargs):
        raise AssertionError("claim parser should not run after consensus failure")

    monkeypatch.setattr(agent_mod, "parse_claimed_answer", fail_parse)

    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=FakeSmtGenerator(),
        z3_runner=FakeZ3(["SAT"]),
        config=AgentConfig(require_claimspec_consensus=True),
    )

    result = agent.run(
        "In USD millions, what was the change in revenue from 2021 to 2022?",
        "The change was -2.",
        "revenue 2021 10\nrevenue 2022 8",
    )

    assert result.status == "ABSTAIN"
    assert result.failure_reason == "claimspec_consensus_failed"
    assert result.metric == "revenue_change"
    assert result.diagnostics["claimspec_consensus"]["failure_reason"] == "formula_mismatch"


def test_ambiguous_operation_abstains_before_claim_parse(monkeypatch):
    claim_spec = ClaimSpec(
        metric="period_change",
        formula="",
        roles=[],
        claim_unit="",
        tolerance=0.01,
        formula_source="no_formula",
        operation="ambiguous_operation",
    )

    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: claim_spec)

    def fail_parse(*args, **kwargs):
        raise AssertionError("claim parser should not run for ambiguous operations")

    monkeypatch.setattr(agent_mod, "parse_claimed_answer", fail_parse)

    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=FakeSmtGenerator(),
        z3_runner=FakeZ3(["SAT"]),
    )

    result = agent.run(
        "what is the decline from current future minimum lease payments and the following years expected obligation?",
        "The decline from 2007 to 2008 is 1703 - 1371 = 332",
        "2007 | 1703\n2008 | 1371",
    )

    assert result.status == "ABSTAIN"
    assert result.failure_reason == "ambiguous_operation"
