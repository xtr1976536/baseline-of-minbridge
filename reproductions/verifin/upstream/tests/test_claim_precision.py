"""The SMT payload uses the post-contract displayed claim exactly.

Question precision is enforced before SMT by the output contract. SMT generation must
not do hidden rounding, because that would verify a value the LLM did not output.
"""
import unittest
from types import SimpleNamespace

from verifiqa.verification.smt_generator import _payload_ir


def _ir(claimed_value, precision_digits):
    fact = SimpleNamespace(value=1.0, unit="USD")
    return SimpleNamespace(
        metric="return_on_assets",
        formula="net_income / assets",
        facts={"net_income": fact},
        claimed_value=claimed_value,
        claim_unit="ratio",
        tolerance=0.005,
        precision_digits=precision_digits,
        tolerance_source="precision",
        computed_unit="ratio",
        query_type="value",
    )


class ClaimPrecisionTests(unittest.TestCase):
    def test_payload_keeps_claim_exact_even_with_precision(self):
        payload = _payload_ir(_ir(-0.0142, 2))
        self.assertEqual(payload["claim"]["value"], -0.0142)

    def test_already_rounded_claim_unchanged(self):
        self.assertEqual(_payload_ir(_ir(-0.02, 2))["claim"]["value"], -0.02)

    def test_no_precision_keeps_raw_claim(self):
        self.assertEqual(_payload_ir(_ir(-0.0142, None))["claim"]["value"], -0.0142)

    def test_none_claim_is_safe(self):
        self.assertIsNone(_payload_ir(_ir(None, 2))["claim"]["value"])


if __name__ == "__main__":
    unittest.main()
