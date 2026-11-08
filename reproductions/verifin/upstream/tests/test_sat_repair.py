"""Z3 verification tests for the claims that the old deterministic repair used to handle.

The deterministic _repair_claim_value logic is replaced by LLM-based repair using
Z3 unsat-cores. These tests verify that Z3 returns SAT (claim verified) when the
correct (rounded) claimed value is used — independent of how that value is obtained.
"""
import unittest
from decimal import Decimal, ROUND_HALF_UP

from verifiqa.types import Claim, VerificationSchema
from verifiqa.verification.z3_runner import Z3Runner

from smt_helpers import render_counterexample_smt


def _round_to_digits(value: float, digits: int) -> float:
    quant = Decimal("1").scaleb(-digits)
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))


class CorrectClaimVerificationTests(unittest.TestCase):
    def test_fixed_asset_turnover_correct_value_verifies(self):
        schema = VerificationSchema(
            metric="fixed_asset_turnover_ratio",
            formula="revenue_2018 / ((ppe_2018 + ppe_2017) / 2)",
            allowed_variables=["computed_fixed_asset_turnover_ratio", "ppe_2017", "ppe_2018", "revenue_2018"],
            required_evidence=["ppe_2017", "ppe_2018", "revenue_2018"],
            allowed_operators=["+", "-", "*", "/", "=", "<=", ">=", "<", ">", "or", "and"],
            tolerance=0.005,
            unit_policy="answer_spec:ratio",
            period_policy="certificate_supplied",
            precision_digits=2,
            claim_unit="ratio",
            computed_unit="ratio",
        )
        variables = {"ppe_2017": 10292.0, "ppe_2018": 11349.0, "revenue_2018": 194579.0}
        correct_value = _round_to_digits(17.982440737489025, 2)
        claim = Claim(schema.metric, correct_value, variables=variables)

        result = Z3Runner().run(render_counterexample_smt(claim, schema))

        self.assertEqual(correct_value, 17.98)
        self.assertEqual(result.solver_status, "SAT")

    def test_cash_conversion_cycle_correct_value_verifies(self):
        schema = VerificationSchema(
            metric="cash_conversion_cycle",
            formula=(
                "365 * ((inventory_2019 + inventory_2018) / 2) / cogs_2019 + "
                "365 * ((receivables_2019 + receivables_2018) / 2) / revenue_2019 - "
                "365 * ((accounts_payable_2019 + accounts_payable_2018) / 2) / "
                "(cogs_2019 + (inventory_2019 - inventory_2018))"
            ),
            allowed_variables=[
                "accounts_payable_2018", "accounts_payable_2019", "cogs_2019",
                "computed_cash_conversion_cycle", "inventory_2018", "inventory_2019",
                "receivables_2018", "receivables_2019", "revenue_2019",
            ],
            required_evidence=[
                "accounts_payable_2018", "accounts_payable_2019", "cogs_2019",
                "inventory_2018", "inventory_2019", "receivables_2018",
                "receivables_2019", "revenue_2019",
            ],
            allowed_operators=["+", "-", "*", "/", "=", "<=", ">=", "<", ">", "or", "and"],
            tolerance=0.005,
            unit_policy="answer_spec:days",
            period_policy="certificate_supplied",
            precision_digits=2,
            claim_unit="days",
            computed_unit="days",
        )
        variables = {
            "accounts_payable_2018": 2746.2, "accounts_payable_2019": 2854.1,
            "cogs_2019": 11108.4, "inventory_2018": 1642.2, "inventory_2019": 1559.3,
            "receivables_2018": 1684.2, "receivables_2019": 1679.7, "revenue_2019": 16865.2,
        }
        correct_value = _round_to_digits(-3.700608203093452, 2)
        claim = Claim(schema.metric, correct_value, variables=variables)

        result = Z3Runner().run(render_counterexample_smt(claim, schema))

        self.assertEqual(correct_value, -3.70)
        self.assertEqual(result.solver_status, "SAT")


if __name__ == "__main__":
    unittest.main()
