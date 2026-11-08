import unittest
from argparse import Namespace
from pathlib import Path

from verifiqa.cli import _resolve_xbrl_calculation_dir


class CliXbrlDefaultTests(unittest.TestCase):
    def test_finqa_uses_finqa_xbrl_default(self):
        args = Namespace(no_xbrl_linkbase_smt=False, xbrl_calculations=None)
        self.assertEqual(_resolve_xbrl_calculation_dir(args, is_finqa=True), Path("artifacts/finqa_xbrl"))

    def test_financebench_uses_calculation_linkbases_default(self):
        args = Namespace(no_xbrl_linkbase_smt=False, xbrl_calculations=None)
        self.assertEqual(
            _resolve_xbrl_calculation_dir(args, is_finqa=False),
            Path("artifacts/calculation_linkbases"),
        )

    def test_explicit_and_disabled_options_win(self):
        explicit = Path("custom/xbrl")
        args = Namespace(no_xbrl_linkbase_smt=False, xbrl_calculations=explicit)
        self.assertEqual(_resolve_xbrl_calculation_dir(args, is_finqa=True), explicit)

        disabled = Namespace(no_xbrl_linkbase_smt=True, xbrl_calculations=explicit)
        self.assertIsNone(_resolve_xbrl_calculation_dir(disabled, is_finqa=True))


if __name__ == "__main__":
    unittest.main()
