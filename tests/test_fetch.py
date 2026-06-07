import json
import pytest
from types import SimpleNamespace
from scripts import fetch_sources as fs


class FakeFiling(SimpleNamespace):
    def obj(self): return self._obj
    def text(self): return self._text


def fake_10k():
    return FakeFiling(form="10-K", accession_no="0001-26-1", filing_date="2026-02-26",
                      filing_url="https://sec.gov/x", _text="",
                      _obj={"Item 1": "NVIDIA designs GPUs.", "Item 1A": "Risks.", "Item 7": "MD&A."})


def test_writes_raw_record_and_state(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "RAW", tmp_path)
    (tmp_path / "sec").mkdir()
    new = fs.ingest_filings([fake_10k()])
    assert new == ["nvda-10k-2026-02-26"]
    rec = json.loads((tmp_path / "sec" / "nvda-10k-2026-02-26.json").read_text())
    assert rec["as_of"] == "2026-Q1" and rec["sections"]["Item 1"].startswith("NVIDIA")
    state = json.loads((tmp_path / "_state.json").read_text())
    assert state["nvda-10k-2026-02-26"]["accession"] == "0001-26-1"


def test_incremental_skips_same_accession(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "RAW", tmp_path)
    (tmp_path / "sec").mkdir()
    assert fs.ingest_filings([fake_10k()]) == ["nvda-10k-2026-02-26"]
    assert fs.ingest_filings([fake_10k()]) == []        # second run: no new


def test_calendar_quarter():
    assert fs.calendar_quarter("2026-02-26") == "2026-Q1"
    assert fs.calendar_quarter("2026-11-20") == "2026-Q4"


@pytest.mark.live
def test_live_fetch_nvda(tmp_path, monkeypatch):
    """Live smoke test: fetches real NVDA filings from EDGAR."""
    monkeypatch.setattr(fs, "RAW", tmp_path)
    (tmp_path / "sec").mkdir()
    result = fs.fetch(ticker="NVDA", limit=6)
    assert isinstance(result, list)
    assert len(result) > 0
    # Find any 10-K record
    ten_k_ids = [sid for sid in result if "10k" in sid]
    assert len(ten_k_ids) > 0, "Expected at least one 10-K in results"
    ten_k_file = tmp_path / "sec" / f"{ten_k_ids[0]}.json"
    assert ten_k_file.exists()
    rec = json.loads(ten_k_file.read_text())
    assert rec["sections"].get("Item 1", ""), "Item 1 must be non-empty for 10-K"
