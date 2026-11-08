import json
from pathlib import Path

import verifiqa.agent.agent as agent_mod
from verifiqa.agent.agent import (
    AgentConfig,
    VerificationAgent,
    _bind_xbrl_role_facts,
    _maybe_authorize_xbrl_linkbase_claim,
)
from verifiqa.agent.types import ClaimedAnswer, ClaimSpec
from verifiqa.types import SolverResult


FIXTURES = Path(__file__).with_name("fixtures") / "xbrl_claimspec"
DOC_NAME = "SYNTHETIC_2025_10K"
QUESTION = (
    "What was Example Company's FY2025 income before income taxes, in USD millions? "
    "Round to the nearest million."
)
ANSWER = "$1,000 million"
EVIDENCE_TEXT = """\
EXAMPLE COMPANY — synthetic filing excerpt. All amounts in millions of USD.

INCOME BEFORE INCOME TAXES
                                                      2025
Income Loss from Continuing Operations before Income Taxes Domestic        (40)
Income Loss from Continuing Operations before Income Taxes Foreign       1,040
Income before income taxes                                           [redacted]
"""


class FakeSmtGenerator:
    def __init__(self):
        self.irs = []

    def generate_ir(self, ir):
        self.irs.append(ir)
        return "(set-logic QF_NRA)\n(check-sat)"


class FakeZ3:
    def run(self, smtlib, label=""):
        return SolverResult(solver_status="SAT")


def _synthetic_xbrl_case(tmp_path: Path) -> tuple[dict, Path]:
    """Build a portable manifest around the minimal checked-in XBRL fixture."""
    artifacts_dir = tmp_path / "xbrl_artifacts"
    artifacts_dir.mkdir()
    manifest = {
        "docs": {
            DOC_NAME: {
                "doc_name": DOC_NAME,
                "instances": [
                    {"status": "saved", "path": str(FIXTURES / "instance.xml")}
                ],
                "calculation_linkbases": [
                    {"status": "saved", "path": str(FIXTURES / "calculation.xml")}
                ],
            }
        }
    }
    (artifacts_dir / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    row = {
        "doc_name": DOC_NAME,
        "question": QUESTION,
        "answer": ANSWER,
        "evidence": [{"evidence_text": EVIDENCE_TEXT}],
    }
    return row, artifacts_dir


def test_xbrl_claimspec_tiebreak_prefers_domestic_foreign_tax_group(tmp_path):
    row, xbrl_artifacts = _synthetic_xbrl_case(tmp_path)
    evidence_text = row["evidence"][0]["evidence_text"]
    seed = ClaimSpec(
        metric="",
        formula="",
        roles=[],
        claim_unit="USD millions",
        tolerance=1.0,
        formula_source="no_formula",
    )

    claim_spec, diagnostics = _maybe_authorize_xbrl_linkbase_claim(
        seed,
        row["question"],
        evidence_text,
        row["doc_name"],
        xbrl_artifacts,
    )

    assert diagnostics["xbrl_claimspec_status"] == "ok"
    assert claim_spec.formula_source == "xbrl_linkbase"
    assert diagnostics["xbrl_claimspec_children"] == [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign",
    ]
    assert "domestic" in claim_spec.formula
    assert "foreign" in claim_spec.formula


def test_xbrl_role_facts_bind_from_exact_child_concepts(tmp_path):
    row, xbrl_artifacts = _synthetic_xbrl_case(tmp_path)
    evidence_text = row["evidence"][0]["evidence_text"]
    seed = ClaimSpec(
        metric="",
        formula="",
        roles=[],
        claim_unit="USD millions",
        tolerance=1.0,
        formula_source="no_formula",
    )
    claim_spec, _diagnostics = _maybe_authorize_xbrl_linkbase_claim(
        seed,
        row["question"],
        evidence_text,
        row["doc_name"],
        xbrl_artifacts,
    )

    facts, diagnostics = _bind_xbrl_role_facts(
        claim_spec, row["doc_name"], xbrl_artifacts
    )

    assert diagnostics["xbrl_role_fact_binding"]["status"] == "ok"
    assert facts["income_loss_from_continuing_operations_before_income_taxes_domestic_fy2025"].value == -40.0
    assert facts["income_loss_from_continuing_operations_before_income_taxes_foreign_fy2025"].value == 1040.0
    assert all(fact.fact_type == "xbrl_numeric" for fact in facts.values())


def test_agent_uses_xbrl_role_binding_before_llm_text_extraction(monkeypatch, tmp_path):
    row, xbrl_artifacts = _synthetic_xbrl_case(tmp_path)
    evidence_text = row["evidence"][0]["evidence_text"]
    seed = ClaimSpec(
        metric="",
        formula="",
        roles=[],
        claim_unit="USD millions",
        tolerance=1.0,
        formula_source="no_formula",
    )
    monkeypatch.setattr(agent_mod, "decompose_question", lambda *args, **kwargs: seed)
    monkeypatch.setattr(
        agent_mod,
        "parse_claimed_answer",
        lambda *args, **kwargs: ClaimedAnswer(value=1000.0, unit="USD millions"),
    )

    def fail_text_extraction(*args, **kwargs):
        raise AssertionError("text extractor should not run when exact XBRL facts bind")

    monkeypatch.setattr(agent_mod, "extract_facts_parallel", fail_text_extraction)

    smt = FakeSmtGenerator()
    agent = VerificationAgent(
        llm_client=object(),
        smt_generator=smt,
        z3_runner=FakeZ3(),
        config=AgentConfig(xbrl_artifacts_dir=xbrl_artifacts),
    )

    result = agent.run(row["question"], row["answer"], evidence_text, doc_name=row["doc_name"])

    assert result.status == "VERIFIED"
    assert result.diagnostics["xbrl_role_fact_binding"]["status"] == "ok"
    assert result.facts["income_loss_from_continuing_operations_before_income_taxes_domestic_fy2025"].value == -40.0
    assert result.facts["income_loss_from_continuing_operations_before_income_taxes_foreign_fy2025"].value == 1040.0
    assert smt.irs[0].facts["income_loss_from_continuing_operations_before_income_taxes_domestic_fy2025"].concept
