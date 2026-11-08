"""Build a FinanceBench-style Apple two-filing numerical reasoning dataset.

The dataset is intentionally oracle-evidence based: each row embeds the exact
EDGAR XBRL facts needed to compute the answer, so the agent can run through the
existing FinanceBench JSONL path without retrieval setup.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from textwrap import wrap
from typing import Any, Iterable, Optional


CIK = "0000320193"
COMPANY = "Apple Inc."
COMPANY_SHORT = "Apple"
DATASET_ID_PREFIX = "apple_two_year"
DEFAULT_OUT = Path("data/apple_two_year_financebench")
SEC_SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
SEC_COMPANYFACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
TARGET_COUNT = 200


def _require_sec_user_agent() -> str:
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required for SEC EDGAR requests; set it to a "
            "descriptive value that includes contact information."
        )
    return user_agent

CURATED_US_GAAP_CONCEPTS = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": "net sales",
    "CostOfGoodsAndServicesSold": "cost of sales",
    "GrossProfit": "gross profit",
    "ResearchAndDevelopmentExpense": "research and development expense",
    "SellingGeneralAndAdministrativeExpense": "selling, general and administrative expense",
    "OperatingExpenses": "operating expenses",
    "OperatingIncomeLoss": "operating income",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "income before income taxes",
    "IncomeTaxExpenseBenefit": "income tax expense",
    "NetIncomeLoss": "net income",
    "CashAndCashEquivalentsAtCarryingValue": "cash and cash equivalents",
    "MarketableSecuritiesCurrent": "current marketable securities",
    "AccountsReceivableNetCurrent": "accounts receivable",
    "InventoryNet": "inventories",
    "AssetsCurrent": "current assets",
    "PropertyPlantAndEquipmentNet": "property, plant, and equipment, net",
    "MarketableSecuritiesNoncurrent": "non-current marketable securities",
    "Assets": "total assets",
    "AccountsPayableCurrent": "accounts payable",
    "LongTermDebtCurrent": "current long-term debt",
    "LiabilitiesCurrent": "current liabilities",
    "LongTermDebtNoncurrent": "non-current long-term debt",
    "LongTermDebt": "total long-term debt",
    "Liabilities": "total liabilities",
    "StockholdersEquity": "stockholders' equity",
    "NetCashProvidedByUsedInOperatingActivities": "net cash provided by operating activities",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capital expenditures",
    "NetCashProvidedByUsedInInvestingActivities": "net cash used in investing activities",
    "PaymentsForRepurchaseOfCommonStock": "share repurchases",
    "PaymentsOfDividends": "dividends paid",
    "NetCashProvidedByUsedInFinancingActivities": "net cash used in financing activities",
    "DepreciationDepletionAndAmortization": "depreciation and amortization",
    "ShareBasedCompensation": "share-based compensation expense",
    "IncomeTaxesPaidNet": "cash paid for income taxes",
}

YOY_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "CostOfGoodsAndServicesSold",
    "GrossProfit",
    "ResearchAndDevelopmentExpense",
    "SellingGeneralAndAdministrativeExpense",
    "OperatingExpenses",
    "OperatingIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeTaxExpenseBenefit",
    "NetIncomeLoss",
    "CashAndCashEquivalentsAtCarryingValue",
    "MarketableSecuritiesCurrent",
    "AccountsReceivableNetCurrent",
    "InventoryNet",
    "AssetsCurrent",
    "PropertyPlantAndEquipmentNet",
    "MarketableSecuritiesNoncurrent",
    "Assets",
    "AccountsPayableCurrent",
    "LongTermDebtCurrent",
    "LiabilitiesCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "Liabilities",
    "StockholdersEquity",
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsOfDividends",
    "DepreciationDepletionAndAmortization",
    "ShareBasedCompensation",
]

PERCENT_OF_REVENUE = [
    "CostOfGoodsAndServicesSold",
    "GrossProfit",
    "ResearchAndDevelopmentExpense",
    "SellingGeneralAndAdministrativeExpense",
    "OperatingExpenses",
    "OperatingIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeTaxExpenseBenefit",
    "NetIncomeLoss",
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsOfDividends",
    "DepreciationDepletionAndAmortization",
    "ShareBasedCompensation",
]

PERCENT_OF_ASSETS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "MarketableSecuritiesCurrent",
    "AccountsReceivableNetCurrent",
    "InventoryNet",
    "AssetsCurrent",
    "PropertyPlantAndEquipmentNet",
    "MarketableSecuritiesNoncurrent",
    "AccountsPayableCurrent",
    "LiabilitiesCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "Liabilities",
    "StockholdersEquity",
]

PERCENT_OF_CURRENT_ASSETS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "MarketableSecuritiesCurrent",
    "AccountsReceivableNetCurrent",
    "InventoryNet",
]

PERCENT_OF_LIABILITIES = [
    "AccountsPayableCurrent",
    "LongTermDebtCurrent",
    "LiabilitiesCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
]


@dataclass(frozen=True)
class Filing:
    fiscal_year: int
    accession: str
    filing_date: str
    report_date: str
    primary_document: str
    doc_name: str


@dataclass(frozen=True)
class Fact:
    fact_id: str
    label: str
    namespace: str
    concept: str
    unit: str
    value: float
    value_millions: float
    fiscal_year: int
    accession: str
    filing_date: str
    report_date: str
    start: str
    end: str
    form: str
    fp: str
    frame: str
    doc_name: str


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--count", type=int, default=TARGET_COUNT)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    out_dir: Path = args.out
    data_dir = out_dir / "data"
    raw_dir = out_dir / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    submissions = _fetch_json(
        SEC_SUBMISSIONS_URL,
        raw_dir / f"sec_submissions_CIK{CIK}.json",
        force=args.force_download,
    )
    time.sleep(0.15)
    companyfacts = _fetch_json(
        SEC_COMPANYFACTS_URL,
        raw_dir / f"sec_companyfacts_CIK{CIK}.json",
        force=args.force_download,
    )

    filings = _latest_10k_filings(submissions, limit=2)
    filing_documents = _download_filing_documents(filings, out_dir, force=args.force_download)
    facts = _extract_current_usd_facts(companyfacts, filings)
    rows = _build_questions(facts, filings, count=args.count)
    if len(rows) < args.count:
        raise RuntimeError(f"Only generated {len(rows)} rows; requested {args.count}")

    questions_path = data_dir / "financebench_open_source.jsonl"
    with questions_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    source_facts_path = data_dir / "source_facts.jsonl"
    with source_facts_path.open("w", encoding="utf-8") as handle:
        for fact in sorted(facts.values(), key=lambda f: (f.fiscal_year, f.label, f.concept)):
            handle.write(json.dumps(asdict(fact), sort_keys=True, ensure_ascii=True) + "\n")

    manifest = {
        "dataset": "apple_two_year_financebench",
        "company": COMPANY,
        "cik": CIK,
        "source": {
            "submissions_url": SEC_SUBMISSIONS_URL,
            "companyfacts_url": SEC_COMPANYFACTS_URL,
        },
        "filings": [asdict(filing) for filing in filings],
        "filing_documents": filing_documents,
        "question_count": len(rows),
        "source_fact_count": len(facts),
        "questions_path": str(questions_path),
        "source_facts_path": str(source_facts_path),
        "reasoning_policy": "Every question uses at least two EDGAR facts and a numerical operation; direct lookup questions are excluded.",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(_readme(manifest), encoding="utf-8")

    print(f"Wrote {len(rows)} questions to {questions_path}")
    print(f"Wrote {len(facts)} source facts to {source_facts_path}")
    print(f"Wrote {len(filing_documents)} filing document bundles under {out_dir}")
    print(f"Wrote manifest to {out_dir / 'manifest.json'}")


def _fetch_json(url: str, path: Path, *, force: bool) -> dict[str, Any]:
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    request = urllib.request.Request(
        url, headers={"User-Agent": _require_sec_user_agent()}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = json.loads(response.read().decode("utf-8"))
    path.write_text(json.dumps(data, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    return data


def _fetch_bytes(url: str, path: Path, *, force: bool) -> bytes:
    if path.exists() and not force:
        return path.read_bytes()
    request = urllib.request.Request(
        url, headers={"User-Agent": _require_sec_user_agent()}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    path.write_bytes(data)
    return data


def _download_filing_documents(
    filings: list[Filing],
    out_dir: Path,
    *,
    force: bool,
) -> list[dict[str, Any]]:
    filings_dir = out_dir / "filings"
    pdf_dir = out_dir / "pdfs"
    filings_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    bundles: list[dict[str, Any]] = []
    for filing in filings:
        accession_no_dash = filing.accession.replace("-", "")
        archive_base = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{accession_no_dash}"
        primary_url = f"{archive_base}/{filing.primary_document}"
        complete_url = f"{archive_base}/{filing.accession}.txt"
        primary_path = filings_dir / f"{filing.doc_name}.htm"
        complete_path = filings_dir / f"{filing.doc_name}.txt"
        pdf_path = pdf_dir / f"{filing.doc_name}.pdf"

        html_bytes = _fetch_bytes(primary_url, primary_path, force=force)
        time.sleep(0.15)
        _fetch_bytes(complete_url, complete_path, force=force)
        text = _html_to_text(html_bytes, title=f"{COMPANY} FY{filing.fiscal_year} Form 10-K")
        _render_text_pdf(
            text,
            pdf_path,
            title=f"{COMPANY} FY{filing.fiscal_year} Form 10-K",
            force=force,
        )
        bundles.append(
            {
                "fiscal_year": filing.fiscal_year,
                "accession": filing.accession,
                "archive_base_url": archive_base,
                "primary_document_url": primary_url,
                "complete_submission_text_url": complete_url,
                "primary_html_path": str(primary_path),
                "complete_submission_text_path": str(complete_path),
                "rendered_pdf_path": str(pdf_path),
                "rendered_pdf_source": "SEC primary filing HTML converted locally to PDF text pages",
            }
        )
        time.sleep(0.15)
    return bundles


class _TextExtractor(HTMLParser):
    SKIP_TAGS = {
        "head",
        "ix:header",
        "ix:hidden",
        "ix:references",
        "ix:resources",
        "noscript",
        "script",
        "style",
    }
    BLOCK_TAGS = {
        "address", "article", "aside", "br", "caption", "div", "footer", "h1",
        "h2", "h3", "h4", "h5", "h6", "header", "li", "p", "section", "table",
        "tbody", "td", "tfoot", "th", "thead", "tr",
    }

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if self._skip_depth == 0 and tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if self._skip_depth == 0 and tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data)

    def text(self) -> str:
        text = "".join(self._parts).replace("\xa0", " ")
        lines = [" ".join(line.split()) for line in text.splitlines()]
        clean: list[str] = []
        blank = False
        for line in lines:
            if not line:
                if not blank:
                    clean.append("")
                blank = True
                continue
            clean.append(line)
            blank = False
        return "\n".join(clean).strip()


def _html_to_text(html_bytes: bytes, *, title: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_bytes.decode("utf-8", errors="replace"))
    body = parser.text()
    return f"{title}\nSource: SEC EDGAR primary filing document\n\n{body}"


def _render_text_pdf(text: str, path: Path, *, title: str, force: bool) -> None:
    if path.exists() and not force:
        return
    try:
        import fitz
    except Exception as exc:  # pragma: no cover - environment guard
        raise RuntimeError("PyMuPDF is required to render filing PDFs") from exc

    doc = fitz.open()
    page_width = 612
    page_height = 792
    margin = 42
    y_start = 44
    y_limit = page_height - 42
    font_size = 8
    line_height = 10
    wrap_width = 112

    page = doc.new_page(width=page_width, height=page_height)
    y = y_start
    page_no = 1

    def new_page() -> Any:
        nonlocal y, page_no
        _footer(page, page_no, title)
        page_no += 1
        y = y_start
        return doc.new_page(width=page_width, height=page_height)

    for raw_line in text.splitlines():
        pieces = wrap(raw_line, width=wrap_width, replace_whitespace=False) or [""]
        for line in pieces:
            if y >= y_limit:
                page = new_page()
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            page.insert_text(
                (margin, y),
                safe_line,
                fontsize=font_size,
                fontname="courier",
                color=(0, 0, 0),
            )
            y += line_height
    _footer(page, page_no, title)
    doc.save(path)
    doc.close()


def _footer(page: Any, page_no: int, title: str) -> None:
    footer = f"{title} | rendered from SEC primary filing HTML | page {page_no}"
    page.insert_text((42, 774), footer[:120], fontsize=7, fontname="helv", color=(0.35, 0.35, 0.35))


def _latest_10k_filings(submissions: dict[str, Any], *, limit: int) -> list[Filing]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_docs = recent.get("primaryDocument", [])
    filings: list[Filing] = []
    for index, form in enumerate(forms):
        if form != "10-K":
            continue
        report_date = str(_at(report_dates, index))
        if not report_date or len(report_date) < 4:
            continue
        fiscal_year = int(report_date[:4])
        filings.append(
            Filing(
                fiscal_year=fiscal_year,
                accession=str(_at(accessions, index)),
                filing_date=str(_at(filing_dates, index)),
                report_date=report_date,
                primary_document=str(_at(primary_docs, index)),
                doc_name=f"APPLE_{fiscal_year}_10K",
            )
        )
    filings.sort(key=lambda filing: filing.filing_date, reverse=True)
    selected = filings[:limit]
    if len(selected) != limit:
        raise RuntimeError(f"Expected {limit} Apple 10-K filings, found {len(selected)}")
    return selected


def _at(items: list[Any], index: int) -> Any:
    return items[index] if index < len(items) else ""


def _extract_current_usd_facts(companyfacts: dict[str, Any], filings: list[Filing]) -> dict[str, Fact]:
    by_accession = {filing.accession: filing for filing in filings}
    selected: dict[tuple[int, str, str], Fact] = {}
    facts_tree = companyfacts.get("facts", {})
    for namespace, concepts in facts_tree.items():
        if namespace != "us-gaap":
            continue
        for concept, concept_body in concepts.items():
            if concept not in CURATED_US_GAAP_CONCEPTS:
                continue
            label = CURATED_US_GAAP_CONCEPTS[concept]
            for unit, fact_entries in (concept_body.get("units") or {}).items():
                if unit != "USD":
                    continue
                for entry in fact_entries:
                    accession = str(entry.get("accn") or "")
                    filing = by_accession.get(accession)
                    if filing is None:
                        continue
                    if not _is_current_fy_fact(entry, filing):
                        continue
                    raw_value = entry.get("val")
                    if not isinstance(raw_value, (int, float)) or not math.isfinite(float(raw_value)):
                        continue
                    value = float(raw_value)
                    value_millions = value / 1_000_000.0
                    if abs(value_millions) < 1.0:
                        continue
                    fact = Fact(
                        fact_id=_fact_id(concept, filing.fiscal_year),
                        label=_clean_label(label),
                        namespace=namespace,
                        concept=concept,
                        unit=unit,
                        value=value,
                        value_millions=value_millions,
                        fiscal_year=filing.fiscal_year,
                        accession=accession,
                        filing_date=filing.filing_date,
                        report_date=filing.report_date,
                        start=str(entry.get("start") or ""),
                        end=str(entry.get("end") or ""),
                        form=str(entry.get("form") or ""),
                        fp=str(entry.get("fp") or ""),
                        frame=str(entry.get("frame") or ""),
                        doc_name=filing.doc_name,
                    )
                    key = (filing.fiscal_year, concept, unit)
                    previous = selected.get(key)
                    if previous is None or _preferred_fact_sort_key(fact) > _preferred_fact_sort_key(previous):
                        selected[key] = fact
    return {fact.fact_id: fact for fact in selected.values()}


def _is_current_fy_fact(entry: dict[str, Any], filing: Filing) -> bool:
    if entry.get("form") != "10-K":
        return False
    if entry.get("fp") != "FY":
        return False
    if str(entry.get("accn") or "") != filing.accession:
        return False
    try:
        if int(entry.get("fy")) != filing.fiscal_year:
            return False
    except (TypeError, ValueError):
        return False
    return str(entry.get("end") or "") == filing.report_date


def _preferred_fact_sort_key(fact: Fact) -> tuple[int, int, str]:
    duration_days = 0
    if fact.start and fact.end:
        duration_days = 1
    return (duration_days, len(fact.start), fact.frame)


def _usable_label(label: str, concept: str) -> bool:
    text = f"{label} {concept}".lower()
    bad = [
        "text block",
        "document",
        "entity",
        "axis",
        "member",
        "number of",
        "per share",
        "per basic",
        "per diluted",
        "shares",
        "share,",
        "share)",
        "stock price",
        "par value",
        "percentage",
        "percent",
        "rate",
    ]
    if any(term in text for term in bad):
        return False
    if len(label.strip()) > 92:
        return False
    return True


def _clean_label(label: str) -> str:
    return " ".join(str(label).replace("/", " / ").split())


def _fact_id(concept: str, fiscal_year: int) -> str:
    return f"{_symbol(concept)}_fy{fiscal_year}"


def _symbol(text: str) -> str:
    out = []
    previous_underscore = False
    for char in text:
        if char.isalnum():
            out.append(char.lower())
            previous_underscore = False
        elif not previous_underscore:
            out.append("_")
            previous_underscore = True
    return "".join(out).strip("_")


def _build_questions(
    facts: dict[str, Fact],
    filings: list[Filing],
    *,
    count: int,
) -> list[dict[str, Any]]:
    years = sorted({filing.fiscal_year for filing in filings}, reverse=True)
    if len(years) != 2:
        raise RuntimeError(f"Expected exactly two fiscal years, found {years}")
    current_year, prior_year = years
    rows: list[dict[str, Any]] = []
    seen_questions: set[str] = set()

    def add(row: dict[str, Any]) -> None:
        if len(rows) >= count:
            return
        question = row["question"]
        if question in seen_questions:
            return
        row["financebench_id"] = f"{DATASET_ID_PREFIX}_{len(rows) + 1:04d}"
        rows.append(row)
        seen_questions.add(question)

    facts_by_year = {
        year: sorted(
            [fact for fact in facts.values() if fact.fiscal_year == year],
            key=lambda fact: (_label_key(fact), fact.concept),
        )
        for year in years
    }
    paired = _paired_facts(facts, current_year, prior_year)

    _add_canonical_rows(add, facts, current_year, prior_year)

    for current, prior in paired:
        if len(rows) >= count:
            break
        if prior.value_millions > 0:
            value = (current.value_millions - prior.value_millions) / prior.value_millions * 100.0
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s year-over-year percentage change in "
                        f"{_lower_label(current.label)} from FY{prior_year} to FY{current_year}? "
                        "Round your answer to one decimal place."
                    ),
                    answer=_format_percent(value),
                    formula="(current_year_value - prior_year_value) / prior_year_value * 100",
                    formula_values={
                        "current_year_value": current.value_millions,
                        "prior_year_value": prior.value_millions,
                    },
                    facts=[current, prior],
                    value=value,
                    unit="percent",
                    justification=(
                        f"Year-over-year percentage change = ({_money_num(current.value_millions)} - "
                        f"{_money_num(prior.value_millions)}) / {_money_num(prior.value_millions)} * 100 = "
                        f"{value:.1f}%."
                    ),
                )
            )

    for current, prior in paired:
        if len(rows) >= count:
            break
        value = current.value_millions - prior.value_millions
        if abs(value) < 1.0:
            continue
        add(
            _row(
                question=(
                    f"Using FY{current_year} minus FY{prior_year}, what was the change in "
                    f"{COMPANY_SHORT}'s {_lower_label(current.label)} from FY{prior_year} to "
                    f"FY{current_year}, in USD millions? "
                    "Round your answer to the nearest million."
                ),
                answer=_format_usd_millions(value),
                formula="current_year_value - prior_year_value",
                formula_values={
                    "current_year_value": current.value_millions,
                    "prior_year_value": prior.value_millions,
                },
                facts=[current, prior],
                value=value,
                unit="USD millions",
                justification=(
                    f"Change = FY{current_year} value - FY{prior_year} value = "
                    f"{_money_num(current.value_millions)} - "
                    f"{_money_num(prior.value_millions)} = {_money_num(value)} USD millions."
                ),
            )
        )

    for current, prior in paired:
        if len(rows) >= count:
            break
        if current.value_millions <= 0 or prior.value_millions <= 0:
            continue
        value = (current.value_millions + prior.value_millions) / 2.0
        add(
            _row(
                question=(
                    f"What was the two-year average of {COMPANY_SHORT}'s {_lower_label(current.label)} "
                    f"across FY{prior_year} and FY{current_year}, in USD millions? "
                    "Round your answer to the nearest million."
                ),
                answer=_format_usd_millions(value),
                formula="(current_year_value + prior_year_value) / 2",
                formula_values={
                    "current_year_value": current.value_millions,
                    "prior_year_value": prior.value_millions,
                },
                facts=[current, prior],
                value=value,
                unit="USD millions",
                justification=(
                    f"Two-year average = ({_money_num(current.value_millions)} + "
                    f"{_money_num(prior.value_millions)}) / 2 = {_money_num(value)} USD millions."
                ),
            )
        )

    _add_percent_of_rows(
        add,
        facts,
        years,
        PERCENT_OF_REVENUE,
        denominator_concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        denominator_label="net sales",
    )
    _add_percent_of_rows(
        add,
        facts,
        years,
        PERCENT_OF_ASSETS,
        denominator_concept="Assets",
        denominator_label="total assets",
    )
    _add_percent_of_rows(
        add,
        facts,
        years,
        PERCENT_OF_CURRENT_ASSETS,
        denominator_concept="AssetsCurrent",
        denominator_label="current assets",
    )
    _add_percent_of_rows(
        add,
        facts,
        years,
        PERCENT_OF_LIABILITIES,
        denominator_concept="Liabilities",
        denominator_label="total liabilities",
    )
    _add_named_ratio_rows(add, facts, years)

    return rows[:count]


def _add_percent_of_rows(
    add,
    facts: dict[str, Fact],
    years: list[int],
    numerator_concepts: list[str],
    *,
    denominator_concept: str,
    denominator_label: str,
) -> None:
    for year in years:
        denominator = facts.get(_fact_id(denominator_concept, year))
        if not denominator or denominator.value_millions <= 0:
            continue
        for concept in numerator_concepts:
            numerator = facts.get(_fact_id(concept, year))
            if not numerator or numerator.concept == denominator.concept:
                continue
            if numerator.value_millions <= 0:
                continue
            value = numerator.value_millions / denominator.value_millions * 100.0
            if not (0.01 <= value <= 300.0):
                continue
            add(
                _row(
                    question=(
                        f"In FY{year}, what was {COMPANY_SHORT}'s {_lower_label(numerator.label)} "
                        f"as a percentage of {denominator_label}? Round your answer to one decimal place."
                    ),
                    answer=_format_percent(value),
                    formula="numerator / denominator * 100",
                    formula_values={
                        "numerator": numerator.value_millions,
                        "denominator": denominator.value_millions,
                    },
                    facts=[numerator, denominator],
                    value=value,
                    unit="percent",
                    justification=(
                        f"{numerator.label.capitalize()} as a percentage of {denominator_label} = "
                        f"{_money_num(numerator.value_millions)} / {_money_num(denominator.value_millions)} "
                        f"* 100 = {value:.1f}%."
                    ),
                )
            )


def _add_named_ratio_rows(add, facts: dict[str, Fact], years: list[int]) -> None:
    templates = [
        (
            "cash ratio",
            "CashAndCashEquivalentsAtCarryingValue",
            "LiabilitiesCurrent",
            "cash and cash equivalents divided by current liabilities",
        ),
        (
            "long-term debt-to-equity ratio",
            "LongTermDebt",
            "StockholdersEquity",
            "total long-term debt divided by stockholders' equity",
        ),
        (
            "liabilities-to-equity ratio",
            "Liabilities",
            "StockholdersEquity",
            "total liabilities divided by stockholders' equity",
        ),
        (
            "capital expenditures to operating cash flow ratio",
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "NetCashProvidedByUsedInOperatingActivities",
            "capital expenditures divided by net cash provided by operating activities",
        ),
        (
            "share repurchases to net income ratio",
            "PaymentsForRepurchaseOfCommonStock",
            "NetIncomeLoss",
            "share repurchases divided by net income",
        ),
        (
            "dividend payout ratio",
            "PaymentsOfDividends",
            "NetIncomeLoss",
            "dividends paid divided by net income",
        ),
        (
            "research and development share of operating expenses",
            "ResearchAndDevelopmentExpense",
            "OperatingExpenses",
            "research and development expense divided by operating expenses",
        ),
        (
            "selling, general and administrative share of operating expenses",
            "SellingGeneralAndAdministrativeExpense",
            "OperatingExpenses",
            "selling, general and administrative expense divided by operating expenses",
        ),
        (
            "operating income to gross profit ratio",
            "OperatingIncomeLoss",
            "GrossProfit",
            "operating income divided by gross profit",
        ),
        (
            "net income to operating income ratio",
            "NetIncomeLoss",
            "OperatingIncomeLoss",
            "net income divided by operating income",
        ),
    ]
    for year in years:
        for metric_name, numerator_concept, denominator_concept, definition in templates:
            numerator = facts.get(_fact_id(numerator_concept, year))
            denominator = facts.get(_fact_id(denominator_concept, year))
            if not numerator or not denominator or denominator.value_millions <= 0:
                continue
            value = numerator.value_millions / denominator.value_millions
            if not (0.0 <= value <= 25.0):
                continue
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s FY{year} {metric_name}, defined as "
                        f"{definition}? Round your answer to two decimal places."
                    ),
                    answer=f"{value:.2f}",
                    formula="numerator / denominator",
                    formula_values={
                        "numerator": numerator.value_millions,
                        "denominator": denominator.value_millions,
                    },
                    facts=[numerator, denominator],
                    value=value,
                    unit="ratio",
                    justification=(
                        f"{metric_name.capitalize()} = {_money_num(numerator.value_millions)} / "
                        f"{_money_num(denominator.value_millions)} = {value:.2f}."
                    ),
                )
            )


def _paired_facts(
    facts: dict[str, Fact],
    current_year: int,
    prior_year: int,
) -> list[tuple[Fact, Fact]]:
    by_key: dict[tuple[str, str], dict[int, Fact]] = {}
    for fact in facts.values():
        by_key.setdefault((fact.concept, fact.unit), {})[fact.fiscal_year] = fact
    pairs = []
    for (_, _), by_year in by_key.items():
        current = by_year.get(current_year)
        prior = by_year.get(prior_year)
        if current and prior:
            pairs.append((current, prior))
    pairs.sort(key=lambda pair: (_label_key(pair[0]), pair[0].concept))
    return pairs


def _add_canonical_rows(
    add,
    facts: dict[str, Fact],
    current_year: int,
    prior_year: int,
) -> None:
    for year in (current_year, prior_year):
        def fact(concept: str) -> Optional[Fact]:
            return facts.get(_fact_id(concept, year))

        revenue = (
            fact("RevenueFromContractWithCustomerExcludingAssessedTax")
            or fact("SalesRevenueNet")
            or fact("Revenues")
        )
        gross_profit = fact("GrossProfit")
        operating_income = fact("OperatingIncomeLoss")
        net_income = fact("NetIncomeLoss")
        rnd = fact("ResearchAndDevelopmentExpense")
        sga = fact("SellingGeneralAndAdministrativeExpense")
        cogs = fact("CostOfGoodsAndServicesSold")
        cfo = fact("NetCashProvidedByUsedInOperatingActivities")
        capex = fact("PaymentsToAcquirePropertyPlantAndEquipment")
        current_assets = fact("AssetsCurrent")
        current_liabilities = fact("LiabilitiesCurrent")
        assets = fact("Assets")
        liabilities = fact("Liabilities")
        equity = fact("StockholdersEquity")

        metric_pairs = [
            ("gross margin", gross_profit, revenue),
            ("operating margin", operating_income, revenue),
            ("net profit margin", net_income, revenue),
            ("research and development expense as a percentage of net sales", rnd, revenue),
            ("selling, general and administrative expense as a percentage of net sales", sga, revenue),
            ("cost of goods and services sold as a percentage of net sales", cogs, revenue),
            ("operating cash flow margin", cfo, revenue),
            ("debt-to-assets ratio using total liabilities divided by total assets", liabilities, assets),
            ("equity-to-assets ratio using stockholders' equity divided by total assets", equity, assets),
        ]
        for metric_name, numerator, denominator in metric_pairs:
            if not numerator or not denominator or denominator.value_millions <= 0:
                continue
            value = numerator.value_millions / denominator.value_millions * 100.0
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s FY{year} {metric_name}? "
                        "Round your answer to one decimal place."
                    ),
                    answer=_format_percent(value),
                    formula="numerator / denominator * 100",
                    formula_values={
                        "numerator": numerator.value_millions,
                        "denominator": denominator.value_millions,
                    },
                    facts=[numerator, denominator],
                    value=value,
                    unit="percent",
                    justification=(
                        f"{metric_name.capitalize()} = {_money_num(numerator.value_millions)} / "
                        f"{_money_num(denominator.value_millions)} * 100 = {value:.1f}%."
                    ),
                )
            )

        if cfo and capex:
            value = cfo.value_millions - capex.value_millions
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s FY{year} free cash flow, defined as "
                        "net cash provided by operating activities minus payments to acquire "
                        "property, plant, and equipment, in USD millions?"
                    ),
                    answer=_format_usd_millions(value),
                    formula="operating_cash_flow - capital_expenditures",
                    formula_values={
                        "operating_cash_flow": cfo.value_millions,
                        "capital_expenditures": capex.value_millions,
                    },
                    facts=[cfo, capex],
                    value=value,
                    unit="USD millions",
                    justification=(
                        f"Free cash flow = {_money_num(cfo.value_millions)} - "
                        f"{_money_num(capex.value_millions)} = {_money_num(value)} USD millions."
                    ),
                )
            )

        if current_assets and current_liabilities and current_liabilities.value_millions > 0:
            value = current_assets.value_millions / current_liabilities.value_millions
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s FY{year} current ratio, defined as "
                        "current assets divided by current liabilities? Round your answer to two decimal places."
                    ),
                    answer=f"{value:.2f}",
                    formula="current_assets / current_liabilities",
                    formula_values={
                        "current_assets": current_assets.value_millions,
                        "current_liabilities": current_liabilities.value_millions,
                    },
                    facts=[current_assets, current_liabilities],
                    value=value,
                    unit="ratio",
                    justification=(
                        f"Current ratio = {_money_num(current_assets.value_millions)} / "
                        f"{_money_num(current_liabilities.value_millions)} = {value:.2f}."
                    ),
                )
            )

    current_net_income = facts.get(_fact_id("NetIncomeLoss", current_year))
    current_assets = facts.get(_fact_id("Assets", current_year))
    prior_assets = facts.get(_fact_id("Assets", prior_year))
    current_equity = facts.get(_fact_id("StockholdersEquity", current_year))
    prior_equity = facts.get(_fact_id("StockholdersEquity", prior_year))
    if current_net_income and current_assets and prior_assets:
        average_assets = (current_assets.value_millions + prior_assets.value_millions) / 2.0
        value = current_net_income.value_millions / average_assets * 100.0
        add(
            _row(
                question=(
                    f"What was {COMPANY_SHORT}'s FY{current_year} return on assets, defined as "
                    f"FY{current_year} net income divided by the average of FY{prior_year} and "
                    f"FY{current_year} total assets? Round your answer to one decimal place."
                ),
                answer=_format_percent(value),
                formula="net_income / ((current_assets + prior_assets) / 2) * 100",
                formula_values={
                    "net_income": current_net_income.value_millions,
                    "current_assets": current_assets.value_millions,
                    "prior_assets": prior_assets.value_millions,
                },
                facts=[current_net_income, current_assets, prior_assets],
                value=value,
                unit="percent",
                justification=(
                    f"ROA = {_money_num(current_net_income.value_millions)} / "
                    f"(({_money_num(current_assets.value_millions)} + {_money_num(prior_assets.value_millions)}) / 2) "
                    f"* 100 = {value:.1f}%."
                ),
            )
        )
    if current_net_income and current_equity and prior_equity:
        average_equity = (current_equity.value_millions + prior_equity.value_millions) / 2.0
        if average_equity > 0:
            value = current_net_income.value_millions / average_equity * 100.0
            add(
                _row(
                    question=(
                        f"What was {COMPANY_SHORT}'s FY{current_year} return on equity, defined as "
                        f"FY{current_year} net income divided by the average of FY{prior_year} and "
                        f"FY{current_year} stockholders' equity? Round your answer to one decimal place."
                    ),
                    answer=_format_percent(value),
                    formula="net_income / ((current_equity + prior_equity) / 2) * 100",
                    formula_values={
                        "net_income": current_net_income.value_millions,
                        "current_equity": current_equity.value_millions,
                        "prior_equity": prior_equity.value_millions,
                    },
                    facts=[current_net_income, current_equity, prior_equity],
                    value=value,
                    unit="percent",
                    justification=(
                        f"ROE = {_money_num(current_net_income.value_millions)} / "
                        f"(({_money_num(current_equity.value_millions)} + {_money_num(prior_equity.value_millions)}) / 2) "
                        f"* 100 = {value:.1f}%."
                    ),
                )
            )


def _denominator_facts(facts: list[Fact]) -> list[Fact]:
    priority = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
        "Assets",
        "AssetsCurrent",
        "Liabilities",
        "LiabilitiesCurrent",
        "GrossProfit",
        "OperatingIncomeLoss",
        "NetIncomeLoss",
        "StockholdersEquity",
    ]
    by_concept = {fact.concept: fact for fact in facts if fact.value_millions > 0}
    out = [by_concept[concept] for concept in priority if concept in by_concept]
    if len(out) < 6:
        out.extend(
            fact for fact in facts
            if fact.value_millions > 0 and fact not in out
        )
    return out[:8]


def _row(
    *,
    question: str,
    answer: str,
    formula: str,
    formula_values: dict[str, float],
    facts: list[Fact],
    value: float,
    unit: str,
    justification: str,
) -> dict[str, Any]:
    doc_names = sorted({fact.doc_name for fact in facts})
    evidence_text = _evidence_text(facts)
    return {
        "financebench_id": "",
        "company": COMPANY,
        "doc_name": "_and_".join(doc_names),
        "question_type": "metrics-generated",
        "question_reasoning": "Numerical reasoning",
        "domain_question_num": None,
        "question": question,
        "answer": answer,
        "justification": justification,
        "dataset_subset_label": "APPLE_TWO_YEAR_EDGAR",
        "evidence": [
            {
                "doc_name": "_and_".join(doc_names),
                "evidence_page_num": None,
                "evidence_text": evidence_text,
                "evidence_text_full_page": evidence_text,
                "source": "SEC EDGAR Company Facts API",
            }
        ],
        "ground_truth": {
            "answer": answer,
            "value": value,
            "unit": unit,
            "formula": formula,
            "formula_values": formula_values,
            "facts": [asdict(fact) for fact in facts],
        },
    }


def _evidence_text(facts: list[Fact]) -> str:
    lines = [
        "SEC EDGAR XBRL evidence for Apple Inc. Values are from the SEC Company Facts API.",
        "USD facts below are expressed in USD millions.",
    ]
    for index, fact in enumerate(facts, start=1):
        period = fact.end if not fact.start else f"{fact.start} to {fact.end}"
        lines.append(
            f"Fact {index}: {fact.label} (us-gaap:{fact.concept}) for FY{fact.fiscal_year}; "
            f"Apple {fact.doc_name} accession {fact.accession}, filed {fact.filing_date}, "
            f"period {period}; value {_format_usd_millions(fact.value_millions)}."
        )
    return "\n".join(lines)


def _label_key(fact: Fact) -> str:
    return _lower_label(fact.label).replace("apple ", "")


def _lower_label(label: str) -> str:
    return label[:1].lower() + label[1:]


def _format_percent(value: float) -> str:
    rounded = round(value, 1)
    if rounded == -0.0:
        rounded = 0.0
    return f"{rounded:.1f}%"


def _format_usd_millions(value: float) -> str:
    rounded = int(round(value))
    sign = "-" if rounded < 0 else ""
    return f"{sign}${abs(rounded):,} million"


def _money_num(value: float) -> str:
    return f"{value:,.0f}"


def _readme(manifest: dict[str, Any]) -> str:
    filings = "\n".join(
        f"- FY{filing['fiscal_year']}: accession {filing['accession']}, filed {filing['filing_date']}, report date {filing['report_date']}"
        for filing in manifest["filings"]
    )
    return (
        "# Apple Two-Year FinanceBench-Style Dataset\n\n"
        "This dataset was generated from SEC EDGAR JSON APIs for Apple Inc. "
        "It follows the local FinanceBench JSONL shape used by the VerifiQA agent.\n\n"
        "Filings:\n"
        f"{filings}\n\n"
        "Rows are in `data/financebench_open_source.jsonl`. Each row contains oracle "
        "EDGAR XBRL evidence and a computed `ground_truth` block. The questions are "
        "numerical reasoning questions only: each one uses at least two facts and a "
        "formula such as percent change, difference, average, ratio, margin, or free "
        "cash flow.\n\n"
        "Filing documents are stored in `filings/` as SEC primary HTML and complete "
        "submission text files. The `pdfs/` files are local renderings from the SEC "
        "primary filing HTML, because these Apple EDGAR filing directories do not "
        "include native PDF attachments.\n\n"
        "Run with:\n\n"
        "```bash\n"
        "PYTHONPATH=src python3 -m verifiqa.agent.cli run \\\n"
        "  --data data/apple_two_year_financebench/data/financebench_open_source.jsonl \\\n"
        "  --out results/agent_apple_two_year_200\n"
        "```\n"
    )


if __name__ == "__main__":
    main()
