"""EDGAR companyfacts binding resolves the right fiscal year, value-blind.

A period appears under several `fy` tags (current year in one 10-K, prior year in the
next) and a 10-K reports multiple annual periods. The fiscal-year-N value is the
fy=N filing's primary (latest-ending) period — which matches the dataset's fiscal
labels across any fiscal calendar, with no calendar assumptions and no use of the
LLM-extracted value.
"""
import unittest
from types import SimpleNamespace

from verifiqa.verification.xbrl_linkbase import (
    _edgar_concept_candidates,
    _fiscal_year_for_fact,
    _primary_fy_entry,
)


def _fact(name, value=0.0, row_label=""):
    return SimpleNamespace(name=name, value=value, row_label=row_label, unit="USD millions")


# Best Buy NetIncomeLoss: the offset-1 (January) fiscal year. The 2014-02..2015-01
# period (1233) is tagged fy=2015 in its own 10-K and fy=2016 in the next.
_BESTBUY_NI = {
    "units": {"USD": [
        {"fy": 2015, "fp": "FY", "form": "10-K", "start": "2013-02-03", "end": "2014-02-01", "val": 532e6, "filed": "2015-03-01"},
        {"fy": 2015, "fp": "FY", "form": "10-K", "start": "2014-02-02", "end": "2015-01-31", "val": 1233e6, "filed": "2015-03-01"},
        {"fy": 2016, "fp": "FY", "form": "10-K", "start": "2014-02-02", "end": "2015-01-31", "val": 1233e6, "filed": "2016-03-01"},
        {"fy": 2016, "fp": "FY", "form": "10-K", "start": "2015-02-01", "end": "2016-01-30", "val": 897e6, "filed": "2016-03-01"},
        {"fy": 2015, "fp": "Q1", "form": "10-Q", "start": "2014-02-02", "end": "2014-05-03", "val": 461e6, "filed": "2014-06-01"},
    ]}
}


class FiscalYearLabelTests(unittest.TestCase):
    def test_year_from_fact_name(self):
        self.assertEqual(_fiscal_year_for_fact(_fact("net_earnings_fy2015"), None), "2015")
        self.assertEqual(_fiscal_year_for_fact(_fact("ap_2019"), None), "2019")


class PrimaryFyEntryTests(unittest.TestCase):
    def test_picks_latest_ending_period_of_the_fy_filing(self):
        # fy=2015 filing reports both 2014 (532) and 2015 (1233) annual periods;
        # the fiscal-2015 value is the latest-ending one.
        e = _primary_fy_entry(_BESTBUY_NI, "2015")
        self.assertEqual(e["val"], 1233e6)
        self.assertEqual(e["end"], "2015-01-31")

    def test_same_period_different_fy_tag(self):
        # The 1233 period is also tagged fy=2016 (as prior year), but fy=2016's
        # primary period is 897 — proving we key on the filing's current year.
        self.assertEqual(_primary_fy_entry(_BESTBUY_NI, "2016")["val"], 897e6)

    def test_ignores_quarterly_and_non_10k(self):
        # fp=Q1 / 10-Q entries never count as the annual value.
        e = _primary_fy_entry(_BESTBUY_NI, "2015")
        self.assertEqual(e["fp"], "FY")
        self.assertEqual(e["form"], "10-K")

    def test_missing_year_returns_none(self):
        self.assertIsNone(_primary_fy_entry(_BESTBUY_NI, "2099"))


class ConceptCandidateTests(unittest.TestCase):
    def test_registry_priority_concept_first(self):
        data = {"facts": {"us-gaap": {"NetIncomeLoss": {}, "ProfitLoss": {}}}}
        cands = _edgar_concept_candidates(data, _fact("net_income_fy2022"))
        self.assertEqual(cands[0], ("us-gaap", "NetIncomeLoss", True))

    def test_value_blind(self):
        # Same candidates regardless of the LLM-extracted value.
        data = {"facts": {"us-gaap": {"NetIncomeLoss": {}, "ProfitLoss": {}}}}
        a = _edgar_concept_candidates(data, _fact("net_income_fy2022", value=-505.0))
        b = _edgar_concept_candidates(data, _fact("net_income_fy2022", value=-713.0))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
