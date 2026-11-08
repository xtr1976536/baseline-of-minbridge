"""Binding must not depend on the LLM-extracted value.

The verifier's job is to check the LLM's answer against the filing. If concept
disambiguation peeks at the LLM's number (picks the candidate nearest to it), the
binding agrees with the answer it is supposed to check -> false verification.
These tests pin the value-blind behaviour: the same concept is chosen regardless of
what the LLM value is, driven by the registry's canonical concept order.
"""
import unittest
from types import SimpleNamespace

from verifiqa.verification.xbrl_linkbase import (
    XbrlContext,
    XbrlFact,
    _ordered_concept_locals,
    _prefer_fiscal_period,
    _prefer_registry_priority,
)


def _fact(name, value):
    return SimpleNamespace(name=name, value=value, row_label="", unit="USD millions")


def _cand(local, value):
    return (SimpleNamespace(local_name=local, value=value, concept=f"us-gaap:{local}"), None)


class RegistryPriorityTests(unittest.TestCase):
    def test_net_income_binds_parent_attributable_not_total(self):
        # NetIncomeLike is parent-attributable only: us-gaap:NetIncomeLoss. The
        # consolidated-incl-NCI concept (us-gaap:ProfitLoss) lives in a SEPARATE
        # concept (NetIncomeTotalLike) so return/per-share ratios can't bind it.
        locals_ = _ordered_concept_locals(_fact("net_income_fy2022", 0.0))
        self.assertEqual(locals_[0], "NetIncomeLoss")
        self.assertNotIn("ProfitLoss", locals_)

    def test_picks_canonical_concept_not_value_match(self):
        # 10420: LLM extracted -505 (ProfitLoss); the correct figure is -713
        # (NetIncomeLoss). ProfitLoss is listed first to prove order, not position,
        # decides — and the LLM value matches the WRONG candidate.
        fact = _fact("net_income_fy2022", -505.0)
        cands = [_cand("ProfitLoss", -505.0), _cand("NetIncomeLoss", -713.0)]
        picked = _prefer_registry_priority(cands, fact)
        self.assertEqual([c[0].local_name for c in picked], ["NetIncomeLoss"])

    def test_choice_is_invariant_to_llm_value(self):
        # Same candidates, three different LLM values -> identical concept chosen.
        cands = [_cand("ProfitLoss", -505.0), _cand("NetIncomeLoss", -713.0)]
        chosen = {
            _prefer_registry_priority(cands, _fact("net_income_fy2022", v))[0][0].local_name
            for v in (-505.0, -713.0, 999.0, 0.0)
        }
        self.assertEqual(chosen, {"NetIncomeLoss"})

    def test_unknown_concept_ranks_last(self):
        # A candidate not in the registry bucket must not outrank a canonical one.
        fact = _fact("net_income_fy2022", 0.0)
        cands = [_cand("SomeRandomConcept", 1.0), _cand("NetIncomeLoss", -713.0)]
        picked = _prefer_registry_priority(cands, fact)
        self.assertEqual([c[0].local_name for c in picked], ["NetIncomeLoss"])

    def test_no_registry_match_keeps_all(self):
        # No bucket for this fact name -> no priority signal -> caller decides.
        fact = _fact("totally_unknown_xyz", 0.0)
        cands = [_cand("Foo", 1.0), _cand("Bar", 2.0)]
        self.assertEqual(len(_prefer_registry_priority(cands, fact)), 2)


def _dur(cid, start, end, value):
    f = XbrlFact(concept=f"us-gaap:NetIncomeLoss", local_name="NetIncomeLoss",
                 context_id=cid, unit_ref="usd", value=value)
    c = XbrlContext(context_id=cid, start_date=start, end_date=end)
    return (f, c)


def _inst(cid, instant, value):
    f = XbrlFact(concept="us-gaap:Assets", local_name="Assets",
                 context_id=cid, unit_ref="usd", value=value)
    c = XbrlContext(context_id=cid, instant=instant)
    return (f, c)


class FiscalPeriodTests(unittest.TestCase):
    def test_full_year_kept_over_quarter(self):
        # 10420: the full-year NetIncomeLoss (-546) must win over quarterly variants,
        # regardless of which value is closer to anything.
        cands = [
            _dur("q1", "2022-01-01", "2022-03-31", -179),
            _dur("fy", "2022-01-01", "2022-12-31", -546),
            _dur("q3", "2022-07-01", "2022-09-30", 421),
        ]
        picked = _prefer_fiscal_period(cands, {"2022"})
        self.assertEqual([f.value for f, _ in picked], [-546])

    def test_year_end_instant_kept_over_interim(self):
        cands = [
            _inst("mar", "2022-03-31", 30000),
            _inst("dec", "2022-12-31", 38363),
        ]
        picked = _prefer_fiscal_period(cands, {"2022"})
        self.assertEqual([f.value for f, _ in picked], [38363])

    def test_no_full_year_match_returns_all(self):
        cands = [_dur("q1", "2022-01-01", "2022-03-31", -179),
                 _dur("q2", "2022-04-01", "2022-06-30", 12)]
        self.assertEqual(len(_prefer_fiscal_period(cands, {"2022"})), 2)

    def test_mixed_period_types_not_resolved_here(self):
        # 06655: a balance (instant) and a flow (full-year duration) for the same
        # loose label must NOT be collapsed by preferring the duration — that picks the
        # wrong concept. Leave both so the binder fails safely instead of mis-binding.
        balance = _inst("dec", "2017-12-31", 34616)
        flow = _dur("fy", "2017-01-01", "2017-12-31", 7175)
        picked = _prefer_fiscal_period([balance, flow], {"2017"})
        self.assertEqual(len(picked), 2)


if __name__ == "__main__":
    unittest.main()
