"""
Download SEC XBRL calculation linkbases and instance documents for FinQA filings.

For each TICKER/YEAR pair in data/finqa/filings.json:
  1. Look up CIK from data/finqa/ticker_cik.json
  2. Find the 10-K filing for that year via SEC submissions API
  3. Download XBRL instance + calculation linkbase
  4. Write manifest to artifacts/finqa_xbrl/manifest.json

Usage:
    python scripts/download_finqa_xbrl.py
    python scripts/download_finqa_xbrl.py --limit 10
    python scripts/download_finqa_xbrl.py --ticker AAPL
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SLEEP = 0.25  # seconds between SEC requests


def _require_sec_user_agent() -> str:
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required for SEC EDGAR requests; set it to a "
            "descriptive value that includes contact information."
        )
    return user_agent


def _fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": _require_sec_user_agent()}
    )
    return urllib.request.urlopen(req, timeout=timeout).read()


def _fetch_json(url: str) -> Any:
    return json.loads(_fetch(url))


def _normalize_cik(cik: str) -> str:
    return str(int(cik)).zfill(10)


def _find_10k_accession(cik: str, year: str) -> str | None:
    """Find the 10-K accession number filed for the given fiscal year."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = _fetch_json(url)
    except Exception:
        return None

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    dates = filings.get("filingDate", [])

    # Also check older filings pages
    pages = data.get("filings", {}).get("files", [])
    if pages:
        for page in pages:
            page_url = f"https://data.sec.gov/submissions/{page['name']}"
            try:
                page_data = _fetch_json(page_url)
                forms += page_data.get("form", [])
                accessions += page_data.get("accessionNumber", [])
                dates += page_data.get("filingDate", [])
                time.sleep(SLEEP)
            except Exception:
                pass

    # Find 10-K filed during or just after the fiscal year
    # FinQA year = fiscal year end year (e.g. 2018 means fiscal year ending in 2018)
    candidates = []
    for form, acc, date in zip(forms, accessions, dates):
        if form not in ("10-K", "10-K405", "10-KSB"):
            continue
        filing_year = date[:4] if date else ""
        # 10-K is usually filed in early next year; accept filings dated year or year+1
        if filing_year in (year, str(int(year) + 1)):
            candidates.append((date, acc))

    if not candidates:
        return None
    # Pick the one closest to the fiscal year end (earliest filing date in range)
    candidates.sort()
    return candidates[0][1]


def _filing_index(cik: str, accession: str) -> dict | None:
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/index.json"
    try:
        return _fetch_json(url)
    except Exception:
        return None


def _files_matching(index: dict, suffixes: tuple[str, ...]) -> list[str]:
    items = index.get("directory", {}).get("item", [])
    return [
        item["name"] for item in items
        if isinstance(item, dict) and any(item.get("name", "").lower().endswith(s) for s in suffixes)
    ]


def _download_file(cik: str, accession: str, filename: str, dest: Path, force: bool) -> dict:
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{filename}"
    entry = {"filename": filename, "url": url, "path": str(dest / filename), "status": "pending"}
    target = dest / filename
    try:
        if target.exists() and not force:
            entry["status"] = "saved"
            entry["bytes"] = target.stat().st_size
            return entry
        payload = _fetch(url)
        target.write_bytes(payload)
        entry["status"] = "saved"
        entry["bytes"] = len(payload)
    except Exception as exc:
        entry["status"] = f"error:{exc}"
    return entry


def download_filing(
    ticker: str,
    year: str,
    cik: str,
    out_dir: Path,
    force: bool = False,
) -> dict:
    doc_name = f"{ticker}_{year}_10K"
    result: dict[str, Any] = {
        "doc_name": doc_name,
        "ticker": ticker,
        "year": year,
        "cik": cik,
        "status": "pending",
    }

    accession = _find_10k_accession(cik, year)
    if not accession:
        result["status"] = "no_10k_found"
        return result
    result["accession"] = accession
    time.sleep(SLEEP)

    index = _filing_index(cik, accession)
    if not index:
        result["status"] = "index_fetch_failed"
        return result
    time.sleep(SLEEP)

    cal_files = _files_matching(index, ("_cal.xml", "-cal.xml"))
    lab_files = _files_matching(index, ("_lab.xml", "-lab.xml"))
    inst_files = [
        f for f in _files_matching(index, (".xml",))
        if not any(f.lower().endswith(s) for s in ("_cal.xml", "_def.xml", "_lab.xml", "_pre.xml", "-cal.xml"))
        and f.lower() != "filingsummary.xml"
    ]

    if not cal_files:
        result["status"] = "no_calculation_linkbase"
        return result
    if not inst_files:
        result["status"] = "no_instance_document"
        return result

    doc_dir = out_dir / doc_name
    doc_dir.mkdir(parents=True, exist_ok=True)

    cal_results, inst_results, lab_results = [], [], []
    for f in cal_files[:1]:
        cal_results.append(_download_file(cik, accession, f, doc_dir, force))
        time.sleep(SLEEP)
    for f in inst_files[:1]:
        inst_results.append(_download_file(cik, accession, f, doc_dir, force))
        time.sleep(SLEEP)
    for f in lab_files[:1]:
        lab_results.append(_download_file(cik, accession, f, doc_dir, force))
        time.sleep(SLEEP)

    result["calculation_linkbases"] = cal_results
    result["instances"] = inst_results
    result["label_linkbases"] = lab_results
    result["status"] = (
        "saved"
        if all(r["status"] == "saved" for r in cal_results + inst_results)
        else "partial"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--filings", type=Path, default=Path("data/finqa/filings.json"))
    parser.add_argument("--ticker-cik", type=Path, default=Path("data/finqa/ticker_cik.json"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/finqa_xbrl"))
    parser.add_argument("--ticker", help="Process only this ticker")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    _require_sec_user_agent()

    filings = json.load(open(args.filings))
    ticker_cik = json.load(open(args.ticker_cik))

    if args.ticker:
        filings = [f for f in filings if f["ticker"] == args.ticker]
    if args.limit:
        filings = filings[: args.limit]

    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "manifest.json"
    existing = {}
    if manifest_path.exists():
        for entry in json.load(open(manifest_path)).get("results", []):
            existing[entry["doc_name"]] = entry

    results = list(existing.values())
    done_names = set(existing)

    total = len(filings)
    for i, f in enumerate(filings, 1):
        ticker, year = f["ticker"], f["year"]
        doc_name = f"{ticker}_{year}_10K"
        if doc_name in done_names and not args.force:
            print(f"[{i}/{total}] {doc_name} already done, skipping")
            continue

        cik = ticker_cik.get(ticker)
        if not cik:
            print(f"[{i}/{total}] {doc_name} — no CIK, skipping")
            results.append({"doc_name": doc_name, "ticker": ticker, "year": year, "status": "no_cik"})
            continue

        cik = _normalize_cik(cik)
        print(f"[{i}/{total}] {doc_name} (CIK {cik}) ...", end=" ", flush=True)
        result = download_filing(ticker, year, cik, args.out, args.force)
        print(result["status"])
        results.append(result)

        # Save manifest after every filing
        manifest = {"n_docs": len(results), "results": results}
        json.dump(manifest, open(manifest_path, "w"), indent=2)

    saved = sum(1 for r in results if r.get("status") == "saved")
    print(f"\nDone. {saved}/{len(results)} saved → {manifest_path}")


if __name__ == "__main__":
    main()
