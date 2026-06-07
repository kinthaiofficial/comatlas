#!/usr/bin/env python3
"""Incrementally pull NVDA filings from EDGAR into raw/sec/ (G5: as_of = calendar quarter).

Real edgartools API notes (5.x):
- Filing.obj() returns TenK / TenQ objects, NOT dicts.
  * TenK properties for text: .business (Item 1), .risk_factors (Item 1A), .management_discussion (Item 7)
  * TenQ: .sections['part_i_item_2'].text() for MD&A
  * 8-K: no structured obj; fall back to f.text()
- An _EdgarFilingAdapter wraps real filings into the same contract that ingest_filings() expects
  (form / accession_no / filing_date / filing_url / obj() / text()), keeping unit tests offline.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"

# Sections to extract per form type (contract used by ingest_filings + unit tests)
SECTIONS = {"10-K": ["Item 1", "Item 1A", "Item 7"], "10-Q": ["Item 2"]}


def calendar_quarter(date_str: str) -> str:
    """Convert a YYYY-MM-DD date to calendar quarter string like '2026-Q1'."""
    y, m, _ = (int(x) for x in str(date_str).split("-"))
    return f"{y}-Q{(m - 1) // 3 + 1}"


def source_id(f) -> str:
    form_slug = f.form.lower().replace("/", "").replace("-", "")
    return f"nvda-{form_slug}-{f.filing_date}"


def _load_state() -> dict:
    p = RAW / "_state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _save_state(s: dict):
    (RAW / "_state.json").write_text(json.dumps(s, indent=2, sort_keys=True))


def ingest_filings(filings) -> list[str]:
    """Process a list of filing objects (real or fake) into raw/sec/ JSON records.

    Each filing must expose:
        .form, .accession_no, .filing_date, .filing_url
        .obj()  -> dict-like with SECTIONS keys  (or None for unsupported forms)
        .text() -> full text fallback
    """
    state, new = _load_state(), []
    for f in filings:
        sid = source_id(f)
        if state.get(sid, {}).get("accession") == f.accession_no:
            continue
        items = SECTIONS.get(f.form, [])
        obj = f.obj() if items else None
        sections = ({i: (obj[i] or "") for i in items} if items
                    else {"body": f.text()[:50_000]})
        rec = {
            "source_id": sid,
            "form": f.form,
            "url": f.filing_url,
            "accession": f.accession_no,
            "filing_date": str(f.filing_date),
            "as_of": calendar_quarter(f.filing_date),
            "sections": sections,
        }
        (RAW / "sec" / f"{sid}.json").write_text(json.dumps(rec, indent=2))
        state[sid] = {"accession": f.accession_no, "processed": False}
        new.append(sid)
    _save_state(state)
    return new


# ---------------------------------------------------------------------------
# Adapter: wraps real edgartools filings into the ingest_filings() contract
# ---------------------------------------------------------------------------

class _EdgarFilingAdapter:
    """Wraps an edgartools EntityFiling so ingest_filings() can consume it."""

    # Maps "Item N" keys used in SECTIONS to TenK named properties
    _TENK_PROP_MAP = {
        "Item 1":  "business",
        "Item 1A": "risk_factors",
        "Item 7":  "management_discussion",
    }
    # Maps "Item N" keys to 10-Q section keys in Sections object
    _TENQ_SECTION_MAP = {
        "Item 2": "part_i_item_2",
    }

    def __init__(self, real_filing):
        self._f = real_filing

    @property
    def form(self):
        return self._f.form

    @property
    def accession_no(self):
        return self._f.accession_no

    @property
    def filing_date(self):
        return str(self._f.filing_date)

    @property
    def filing_url(self):
        return self._f.filing_url or ""

    def obj(self):
        """Return a dict mapping 'Item N' -> text for the form type."""
        real_obj = self._f.obj()
        form = self._f.form
        if form == "10-K":
            result = {}
            for key, prop in self._TENK_PROP_MAP.items():
                val = getattr(real_obj, prop, None)
                result[key] = str(val) if val is not None else ""
            return result
        elif form == "10-Q":
            result = {}
            secs = real_obj.sections
            for key, sec_key in self._TENQ_SECTION_MAP.items():
                sec = secs.get(sec_key) if hasattr(secs, "get") else None
                if sec is None:
                    try:
                        sec = secs[sec_key]
                    except (KeyError, TypeError):
                        sec = None
                if sec is not None:
                    try:
                        result[key] = sec.text() or ""
                    except Exception:
                        result[key] = ""
                else:
                    result[key] = ""
            return result
        else:
            # 8-K and others: no structured items
            return {}

    def text(self):
        try:
            return self._f.text() or ""
        except Exception:
            return ""


def fetch(ticker="NVDA", limit=6) -> list[str]:
    """Fetch real filings from EDGAR and ingest them."""
    from edgar import Company, set_identity   # import here: keep unit tests offline
    set_identity("ComAtlas bot freddy@kinthai.ai")
    raw_filings = Company(ticker).get_filings(form=["10-K", "10-Q", "8-K"]).head(limit)
    adapted = [_EdgarFilingAdapter(f) for f in raw_filings]
    return ingest_filings(adapted)


if __name__ == "__main__":
    print(json.dumps(fetch(*(sys.argv[1:2] or ["NVDA"]))))
