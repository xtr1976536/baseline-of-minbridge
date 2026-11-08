import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from verifiqa.policy.source_builder import (
    TaxonomySource,
    build_policy_source_report,
    load_taxonomy_concepts,
)


def _xsd(*names: str) -> bytes:
    elements = "\n".join(f'  <xs:element name="{name}" />' for name in names)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
        f"{elements}\n"
        "</xs:schema>\n"
    ).encode("utf-8")


def _write_zip(path: Path, *names: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("elts/test.xsd", _xsd(*names))


class PolicySourceBuilderTests(unittest.TestCase):
    def test_load_taxonomy_concepts_from_cached_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            _write_zip(cache_dir / "gaap.zip", "NetIncomeLoss", "Assets")
            source = TaxonomySource(
                source_id="gaap",
                standard="US GAAP",
                publisher="FASB",
                version="test",
                prefixes=("us-gaap",),
                package_url="https://example.test/gaap.zip",
            )

            concepts = load_taxonomy_concepts([source], cache_dir=cache_dir, fetch=False, timeout=1)

        self.assertIn("us-gaap:NetIncomeLoss", concepts)
        self.assertIn("us-gaap:Assets", concepts)

    def test_build_policy_source_report_verifies_seeded_qnames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "policy_data"
            cache_dir = root / "cache"
            data_dir.mkdir()
            _write_zip(cache_dir / "gaap.zip", "NetIncomeLoss", "Assets")
            (data_dir / "taxonomy_sources.json").write_text(
                json.dumps(
                    [
                        {
                            "source_id": "gaap",
                            "standard": "US GAAP",
                            "publisher": "FASB",
                            "version": "test",
                            "prefixes": ["us-gaap"],
                            "package_url": "https://example.test/gaap.zip",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (data_dir / "semantic_concepts.json").write_text(
                json.dumps(
                    [
                        {
                            "concept_id": "NetIncomeLike",
                            "aliases": ["net income"],
                            "xbrl_concepts": ["us-gaap:NetIncomeLoss"],
                        },
                        {
                            "concept_id": "TotalAssetsLike",
                            "aliases": ["assets"],
                            "xbrl_concepts": ["us-gaap:Assets"],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (data_dir / "metric_policies.json").write_text(
                json.dumps(
                    [
                        {
                            "policy_id": "standard_roa_assets",
                            "metric": "roa",
                            "formula_templates": ["net_income / assets"],
                            "roles": {},
                            "source_type": "metric_convention_with_taxonomy_semantics",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = build_policy_source_report(data_dir=data_dir, cache_dir=cache_dir, fetch=False)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["xbrl_concepts"], 2)
        self.assertEqual(report["verified_xbrl_concepts"], 2)
        self.assertEqual(report["missing_xbrl_concepts"], [])


if __name__ == "__main__":
    unittest.main()
