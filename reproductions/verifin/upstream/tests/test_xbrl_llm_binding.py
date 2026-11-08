import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.xbrl_candidate_gen import generate_candidates
from verifiqa.verification.xbrl_linkbase import (
    EdgarCompanyFactsCache,
    FilingXbrl,
    XbrlContext,
    XbrlFact,
    _bind_fact_edgar,
    _bind_fact_local,
    _candidate_concept_locals,
    attach_xbrl_calculations,
    augment_smt_with_xbrl,
)
from verifiqa.verification.xbrl_llm_binder import XbrlLlmBinder


class FailingLlm:
    def chat(self, *args, **kwargs):
        raise AssertionError("LLM should not be called for absence-only binding")


class SelectingLlm:
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id

    def chat(self, *args, **kwargs):
        return json.dumps({
            "bindings": [
                {
                    "fact_name": "ppe_fy2018",
                    "selected_candidate_id": self.candidate_id,
                    "confidence": 1.0,
                    "reason": "matches property plant and equipment net",
                }
            ]
        })


class XbrlLlmBindingTests(unittest.TestCase):

    def test_edgar_cache_requires_user_agent_before_network_request(self):
        EdgarCompanyFactsCache.clear()
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(os.environ, {"SEC_USER_AGENT": ""}),
                patch(
                    "verifiqa.verification.xbrl_linkbase.urllib.request.urlopen"
                ) as urlopen,
            ):
                with self.assertRaisesRegex(RuntimeError, "SEC_USER_AGENT is required"):
                    EdgarCompanyFactsCache.get("987654321", Path(tmp))

        urlopen.assert_not_called()

    def test_registry_concept_locals_use_inferred_concept_ids(self):
        fact = VerificationFact(
            name="cash_from_operations",
            value=1469.502,
            unit="USD millions",
            row_label="Net cash provided by operating activities",
        )

        locals_ = _candidate_concept_locals(fact, None)

        self.assertIn("NetCashProvidedByUsedInOperatingActivities", locals_)

    def test_registry_seed_candidate_survives_without_lexical_overlap(self):
        companyfacts = {
            "facts": {
                "us-gaap": {
                    "NetCashProvidedByUsedInOperatingActivities": {
                        "label": "Net Cash Provided by Used in Operating Activities",
                        "description": "Cash inflow or outflow from operating activities.",
                        "units": {
                            "USD": [
                                {
                                    "start": "2022-01-01",
                                    "end": "2022-12-31",
                                    "val": 1000000,
                                    "accn": "0000000000-23-000001",
                                    "fy": 2022,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2023-02-01",
                                }
                            ]
                        },
                    }
                }
            }
        }

        handles, _value_map, diagnostics = generate_candidates(
            fact_name="opaque_metric",
            source_quote="Opaque reported line 1,000",
            row_label="Opaque reported line",
            target_years={"2022"},
            companyfacts=companyfacts,
            seed_concept_locals={"NetCashProvidedByUsedInOperatingActivities"},
        )

        self.assertEqual(handles[0].concept, "us-gaap:NetCashProvidedByUsedInOperatingActivities")
        self.assertEqual(diagnostics["kept_seed"], 1)

    def test_edgar_percent_fact_rejects_usd_label_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            edgar_dir = Path(tmp)
            (edgar_dir / "CIK0000123456.json").write_text(json.dumps({
                "facts": {
                    "us-gaap": {
                        "UnrecognizedTaxBenefitsThatWouldImpactEffectiveTaxRate": {
                            "label": "Unrecognized Tax Benefits That Would Impact Effective Tax Rate",
                            "units": {
                                "USD": [{
                                    "end": "2022-12-31",
                                    "val": 750000000,
                                    "accn": "0000000000-23-000001",
                                    "fy": 2022,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2023-02-01",
                                }]
                            },
                        }
                    }
                }
            }))
            EdgarCompanyFactsCache.clear()
            fact = VerificationFact(
                name="effective_tax_rate_2022",
                value=21.6,
                unit="percent",
                period="FY2022",
                row_label="Effective tax rate",
            )
            ir = VerificationIR(
                metric="effective_tax_rate_change",
                formula="effective_tax_rate_2022",
                facts={"effective_tax_rate_2022": fact},
                claimed_value=21.6,
                claim_unit="percent",
                tolerance=0.1,
            )

            binding = _bind_fact_edgar(fact, ir, "0000123456", edgar_dir)

        self.assertIsNone(binding)

    def test_edgar_pure_rate_binds_to_percent_fact_with_multiplier(self):
        with tempfile.TemporaryDirectory() as tmp:
            edgar_dir = Path(tmp)
            (edgar_dir / "CIK0000123456.json").write_text(json.dumps({
                "facts": {
                    "us-gaap": {
                        "EffectiveIncomeTaxRateContinuingOperations": {
                            "label": "Effective Income Tax Rate Continuing Operations",
                            "units": {
                                "pure": [{
                                    "end": "2022-12-31",
                                    "val": 0.216,
                                    "accn": "0000000000-23-000001",
                                    "fy": 2022,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2023-02-01",
                                }]
                            },
                        }
                    }
                }
            }))
            EdgarCompanyFactsCache.clear()
            fact = VerificationFact(
                name="effective_tax_rate_2022",
                value=21.6,
                unit="percent",
                period="FY2022",
                row_label="Effective tax rate",
            )
            ir = VerificationIR(
                metric="effective_tax_rate_change",
                formula="effective_tax_rate_2022",
                facts={"effective_tax_rate_2022": fact},
                claimed_value=21.6,
                claim_unit="percent",
                tolerance=0.1,
            )

            binding = _bind_fact_edgar(fact, ir, "0000123456", edgar_dir)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["unit_ref"], "pure")
        self.assertEqual(binding["unit_measures"], ["pure"])
        self.assertEqual(binding["binding_multiplier"], 100.0)
        self.assertEqual(binding["binding_kind"], "ratio_to_percent")
        self.assertAlmostEqual(binding["xbrl_value"], 0.216)

    def test_edgar_rounded_pure_rate_keeps_displayed_percent_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            edgar_dir = Path(tmp)
            (edgar_dir / "CIK0000123456.json").write_text(json.dumps({
                "facts": {
                    "us-gaap": {
                        "EffectiveIncomeTaxRateContinuingOperations": {
                            "label": "Effective Income Tax Rate Continuing Operations",
                            "units": {
                                "pure": [{
                                    "end": "2021-12-31",
                                    "val": 0.205,
                                    "accn": "0000000000-22-000001",
                                    "fy": 2021,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2022-02-01",
                                }]
                            },
                        }
                    }
                }
            }))
            EdgarCompanyFactsCache.clear()
            fact = VerificationFact(
                name="effective_tax_rate_2021",
                value=20.0,
                unit="percent",
                period="FY2021",
                row_label="Effective tax rate",
            )
            ir = VerificationIR(
                metric="effective_tax_rate_change",
                formula="effective_tax_rate_2021",
                facts={"effective_tax_rate_2021": fact},
                claimed_value=20.0,
                claim_unit="percent",
                tolerance=0.5,
            )

            binding = _bind_fact_edgar(fact, ir, "0000123456", edgar_dir)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["binding_multiplier"], 100.0)
        self.assertEqual(binding["binding_kind"], "rounded_ratio_to_percent")
        self.assertEqual(binding["binding_tolerance"], 0.5)

    def test_local_linkbase_binds_signed_capex_to_positive_xbrl_payment(self):
        context_id = "Duration_1_1_2018_To_12_31_2018"
        concept = "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
        xbrl_fact = XbrlFact(
            concept=concept,
            local_name="PaymentsToAcquirePropertyPlantAndEquipment",
            context_id=context_id,
            unit_ref="Unit12",
            decimals="-6",
            value=Decimal("1577000000"),
        )
        bundle = FilingXbrl(
            doc_name="TEST_2018_10K",
            status="ok",
            contexts={
                context_id: XbrlContext(
                    context_id=context_id,
                    start_date="2018-01-01",
                    end_date="2018-12-31",
                )
            },
            units={"Unit12": ("iso4217:USD",)},
            facts_by_local_context={(concept, context_id): xbrl_fact},
        )
        ir = VerificationIR(
            metric="capital_expenditure",
            formula="capex_fy2018",
            claimed_value=1577.0,
            claim_unit="USD millions",
            tolerance=0.5,
            period="FY2018",
            facts={
                "capex_fy2018": VerificationFact(
                    name="capex_fy2018",
                    value=-1577.0,
                    unit="USD millions",
                    source_quote="Purchases of property, plant and equipment (1,577)",
                    chunk_id="cash_flow",
                    period="FY2018",
                    row_label="Purchases of property, plant and equipment",
                )
            },
        )

        binding = _bind_fact_local(ir.facts["capex_fy2018"], ir, bundle)

        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertEqual(binding["concept"], concept)
        self.assertEqual(binding["xbrl_value"], 1577.0)
        self.assertEqual(binding["binding_multiplier"], -1.0)
        self.assertEqual(binding["binding_kind"], "outflow_magnitude")

        ir.xbrl_calculations = {
            "bindings": [binding],
            "constraints": [],
            "declared_variables": [binding["xbrl_variable"]],
        }
        smt = """(set-logic QF_NRA)
(declare-const capex_fy2018 Real)
(assert (! (= capex_fy2018 -1577.0) :named evidence_capex_fy2018))
(check-sat)
"""
        augmented = augment_smt_with_xbrl(smt, ir)

        self.assertIn(
            f"(= capex_fy2018 (* -1 {binding['xbrl_variable']}))",
            augmented,
        )
        self.assertIn(
            f"(= {binding['xbrl_variable']} 1577)",
            augmented,
        )

    def test_numeric_only_mode_binds_local_fact_despite_unit_kind_mismatch(self):
        context_id = "Duration_1_1_2018_To_12_31_2018"
        concept = "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
        xbrl_fact = XbrlFact(
            concept=concept,
            local_name="PaymentsToAcquirePropertyPlantAndEquipment",
            context_id=context_id,
            unit_ref="Unit12",
            decimals="0",
            value=Decimal("1577"),
        )
        bundle = FilingXbrl(
            doc_name="TEST_2018_10K",
            status="ok",
            contexts={
                context_id: XbrlContext(
                    context_id=context_id,
                    start_date="2018-01-01",
                    end_date="2018-12-31",
                )
            },
            units={"Unit12": ("iso4217:USD",)},
            facts_by_local_context={(concept, context_id): xbrl_fact},
        )
        ir = VerificationIR(
            metric="capital_expenditure",
            formula="capex_fy2018",
            claimed_value=1577.0,
            claim_unit="ratio",
            tolerance=0.5,
            period="FY2018",
            facts={
                "capex_fy2018": VerificationFact(
                    name="capex_fy2018",
                    value=1577.0,
                    unit="ratio",
                    period="FY2018",
                    row_label="Purchases of property, plant and equipment",
                )
            },
        )

        default_binding = _bind_fact_local(ir.facts["capex_fy2018"], ir, bundle)
        numeric_only_binding = _bind_fact_local(
            ir.facts["capex_fy2018"],
            ir,
            bundle,
            ignore_unit_matching=True,
        )

        self.assertIsNone(default_binding)
        self.assertIsNotNone(numeric_only_binding)
        assert numeric_only_binding is not None
        self.assertEqual(numeric_only_binding["concept"], concept)
        self.assertEqual(numeric_only_binding["binding_multiplier"], 1.0)

    def test_edgar_primary_binding_connects_to_local_calculation_linkbase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts_dir = root / "calculation_linkbases"
            doc_dir = artifacts_dir / "TEST_2018_10K"
            edgar_dir = root / "edgar_companyfacts"
            doc_dir.mkdir(parents=True)
            edgar_dir.mkdir()
            instance_path = doc_dir / "test-20181231.xml"
            calc_path = doc_dir / "test-20181231_cal.xml"
            context_id = "Duration_1_1_2018_To_12_31_2018"
            instance_path.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2018" xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
  <xbrli:context id="{context_id}">
    <xbrli:period><xbrli:startDate>2018-01-01</xbrli:startDate><xbrli:endDate>2018-12-31</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
  <us-gaap:NetCashProvidedByUsedInInvestingActivities contextRef="{context_id}" unitRef="USD" decimals="-6">-1577000000</us-gaap:NetCashProvidedByUsedInInvestingActivities>
  <us-gaap:PaymentsToAcquirePropertyPlantAndEquipment contextRef="{context_id}" unitRef="USD" decimals="-6">1577000000</us-gaap:PaymentsToAcquirePropertyPlantAndEquipment>
</xbrli:xbrl>
""")
            calc_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:calculationLink xlink:type="extended" xlink:role="http://example.com/role/CashFlow">
    <link:loc xlink:type="locator" xlink:href="http://xbrl.fasb.org/us-gaap/2018/elts/us-gaap-2018-01-31.xsd#us-gaap_NetCashProvidedByUsedInInvestingActivities" xlink:label="parent" />
    <link:loc xlink:type="locator" xlink:href="http://xbrl.fasb.org/us-gaap/2018/elts/us-gaap-2018-01-31.xsd#us-gaap_PaymentsToAcquirePropertyPlantAndEquipment" xlink:label="child" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="parent" xlink:to="child" order="1" weight="-1" />
  </link:calculationLink>
</link:linkbase>
""")
            (artifacts_dir / "manifest.json").write_text(json.dumps({
                "results": [{
                    "doc_name": "TEST_2018_10K",
                    "cik": "0000123456",
                    "instances": [{"status": "saved", "path": str(instance_path)}],
                    "calculation_linkbases": [{"status": "saved", "path": str(calc_path)}],
                }]
            }))
            (edgar_dir / "CIK0000123456.json").write_text(json.dumps({
                "facts": {
                    "us-gaap": {
                        "PaymentsToAcquirePropertyPlantAndEquipment": {
                            "label": "Payments to Acquire Property Plant and Equipment",
                            "units": {
                                "USD": [{
                                    "start": "2018-01-01",
                                    "end": "2018-12-31",
                                    "val": 1577000000,
                                    "accn": "0000000000-19-000001",
                                    "fy": 2018,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2019-02-01",
                                }]
                            },
                        }
                    }
                }
            }))
            EdgarCompanyFactsCache.clear()
            ir = VerificationIR(
                metric="capital_expenditure",
                formula="capex_fy2018",
                claimed_value=1577.0,
                claim_unit="USD millions",
                tolerance=0.5,
                period="FY2018",
                facts={
                    "capex_fy2018": VerificationFact(
                        name="capex_fy2018",
                        value=1577.0,
                        unit="USD millions",
                        source_quote="Purchases of property, plant and equipment 1,577",
                        chunk_id="cash_flow",
                        period="FY2018",
                        row_label="Purchases of property, plant and equipment",
                    )
                },
            )

            attached = attach_xbrl_calculations(ir, "TEST_2018_10K", artifacts_dir)

        xbrl = attached.xbrl_calculations
        self.assertEqual(xbrl["status"], "ok")
        self.assertEqual(xbrl["grounding_status"], "LINKBASE_OK")
        self.assertEqual(xbrl["binding_sources"], ["edgar_companyfacts_fy"])
        self.assertEqual(len(xbrl["bindings"]), 1)
        self.assertEqual(len(xbrl["constraints"]), 1)
        binding = xbrl["bindings"][0]
        self.assertIn("edgar_2018_12_31", binding["source_variable"])
        self.assertNotIn("edgar_2018_12_31", binding["xbrl_variable"])
        child_variables = {child["variable"] for child in xbrl["constraints"][0]["children"]}
        self.assertIn(binding["xbrl_variable"], child_variables)

    def test_llm_binding_preserves_text_extracted_fact_value(self):
        candidate_id = "us-gaap__PropertyPlantAndEquipmentNet__2018-12-31__0000000000-19-000001"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts_dir = root / "calculation_linkbases"
            edgar_dir = root / "edgar_companyfacts"
            artifacts_dir.mkdir()
            edgar_dir.mkdir()
            (artifacts_dir / "manifest.json").write_text(
                json.dumps({"results": [{"doc_name": "TEST_2018_10K", "cik": "0000123456"}]})
            )
            (edgar_dir / "CIK0000123456.json").write_text(json.dumps({
                "facts": {
                    "us-gaap": {
                        "PropertyPlantAndEquipmentNet": {
                            "label": "Property Plant and Equipment Net",
                            "description": "Property, plant and equipment, net of accumulated depreciation.",
                            "units": {
                                "USD": [
                                    {
                                        "end": "2018-12-31",
                                        "val": 282000000,
                                        "accn": "0000000000-19-000001",
                                        "fy": 2018,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "filed": "2019-02-01",
                                    }
                                ]
                            },
                        }
                    }
                }
            }))
            EdgarCompanyFactsCache.clear()

            ir = VerificationIR(
                metric="net_ppe",
                formula="ppe_fy2018",
                claimed_value=285.0,
                claim_unit="USD millions",
                tolerance=0.5,
                period="FY2018",
                facts={
                    "ppe_fy2018": VerificationFact(
                        name="ppe_fy2018",
                        value=285.0,
                        unit="USD millions",
                        source_quote="Property and equipment, net 285",
                        chunk_id="ppe_table",
                        period="FY2018",
                        row_label="Property and equipment, net",
                    )
                },
            )

            bound = XbrlLlmBinder(SelectingLlm(candidate_id), edgar_dir).bind_facts(
                ir,
                "TEST_2018_10K",
                artifacts_dir,
            )

        self.assertEqual(bound.xbrl_calculations["status"], "ok")
        self.assertEqual(bound.facts["ppe_fy2018"].value, 285.0)
        binding = bound.xbrl_calculations["bindings"][0]
        self.assertEqual(binding["llm_original_value"], 285.0)
        self.assertEqual(binding["xbrl_value"], 282.0)

    def test_absence_only_fact_is_ok_without_llm_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts_dir = root / "calculation_linkbases"
            edgar_dir = root / "edgar_companyfacts"
            artifacts_dir.mkdir()
            edgar_dir.mkdir()
            (artifacts_dir / "manifest.json").write_text(
                json.dumps({"results": [{"doc_name": "AES_2022_10K", "cik": "0000874761"}]})
            )
            (edgar_dir / "CIK0000874761.json").write_text(json.dumps({"facts": {}}))
            EdgarCompanyFactsCache.clear()

            ir = VerificationIR(
                metric="restructuring_costs",
                formula="restructuring_costs",
                claimed_value=0.0,
                claim_unit="USD millions",
                tolerance=0.5,
                period="FY2022",
                facts={
                    "restructuring_costs": VerificationFact(
                        name="restructuring_costs",
                        value=0.0,
                        unit="USD millions",
                        fact_type="absence_implies_zero",
                        source_quote="Consolidated Statements of Operations 2022 Revenue Cost of Sales Interest expense Income loss",
                        chunk_id="aes_stmt",
                        period="FY2022",
                        row_label="Restructuring costs",
                        absence_scope={
                            "metric": "restructuring costs",
                            "period": "FY2022",
                            "statement": "Consolidated Statements of Operations",
                        },
                    )
                },
            )

            bound = XbrlLlmBinder(FailingLlm(), edgar_dir).bind_facts(
                ir,
                "AES_2022_10K",
                artifacts_dir,
            )

        xbrl = bound.xbrl_calculations
        self.assertEqual(xbrl["status"], "ok")
        self.assertEqual(xbrl["bindings"], [])
        self.assertEqual(xbrl["absence_witnesses"][0]["fact_name"], "restructuring_costs")


if __name__ == "__main__":
    unittest.main()
