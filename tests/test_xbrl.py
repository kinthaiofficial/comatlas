"""Tests for leg_xbrl.py — pure logic unit tests + live smoke."""
import pytest
from scripts.extract import leg_xbrl

FIN = {
    "revenue": 130_497_000_000,
    "segments": {"Compute & Networking": 116_000_000_000, "Graphics": 14_497_000_000},
}


def test_facts_and_segment_edges():
    facts, edges = leg_xbrl.to_facts_edges(
        FIN,
        entity="nvidia",
        period="FY2026",
        source="nvda-10k-2026-02-26",
        as_of="2026-Q1",
    )
    assert {
        "metric": "revenue",
        "value": 130_497_000_000,
        "unit": "USD",
        "period": "FY2026",
        "source": "nvda-10k-2026-02-26",
        "confidence": "high",
        "extractors": ["xbrl"],
    } in facts

    seg = [e for e in edges if e["predicate"] == "IN_SEGMENT"]
    assert {
        "subject": "nvidia-compute-networking",
        "subject_type": "Segment",
        "predicate": "IN_SEGMENT",
        "target": "nvidia",
        "target_type": "Company",
        "as_of": "2026-Q1",
        "source": "nvda-10k-2026-02-26",
        "from_structured": True,
        "extractor": "xbrl",
        "evidence": "XBRL reportable segment: Compute & Networking",
    } in seg

    assert any(f["metric"] == "segment_revenue:nvidia-compute-networking" for f in facts)


def test_graphics_segment_resolved_via_alias():
    """'Graphics' should resolve via alias_map to nvidia-graphics (known=True)."""
    _, edges = leg_xbrl.to_facts_edges(
        FIN,
        entity="nvidia",
        period="FY2026",
        source="nvda-10k-2026-02-26",
        as_of="2026-Q1",
    )
    seg = [e for e in edges if e["predicate"] == "IN_SEGMENT"]
    assert any(e["subject"] == "nvidia-graphics" for e in seg)


def test_unknown_segment_prefixed():
    """Segments not in alias_map get company-prefixed ids (G10)."""
    fin = {"revenue": 1_000_000, "segments": {"Widget Division": 600_000}}
    facts, edges = leg_xbrl.to_facts_edges(
        fin,
        entity="acme",
        period="FY2025",
        source="acme-10k-2025",
        as_of="2025-Q4",
    )
    seg = [e for e in edges if e["predicate"] == "IN_SEGMENT"]
    assert seg[0]["subject"] == "acme-widget-division"
    assert any(f["metric"] == "segment_revenue:acme-widget-division" for f in facts)


def test_no_segments():
    """fin with no segments key still returns revenue fact and empty edges."""
    fin = {"revenue": 50_000_000}
    facts, edges = leg_xbrl.to_facts_edges(
        fin,
        entity="smallco",
        period="FY2024",
        source="smallco-10k-2024",
        as_of="2024-Q4",
    )
    assert any(f["metric"] == "revenue" for f in facts)
    assert edges == []


def test_revenue_fact_has_no_extra_keys():
    """Revenue fact must match exactly — no extra keys allowed."""
    facts, _ = leg_xbrl.to_facts_edges(
        FIN,
        entity="nvidia",
        period="FY2026",
        source="nvda-10k-2026-02-26",
        as_of="2026-Q1",
    )
    rev = next(f for f in facts if f["metric"] == "revenue")
    assert set(rev.keys()) == {"metric", "value", "unit", "period", "source", "confidence", "extractors"}


@pytest.mark.live
def test_extract_live_nvda():
    """Live smoke: extract() on real raw/sec/nvda-10k-2026-02-25.json."""
    import json
    from pathlib import Path

    raw_path = Path(__file__).resolve().parents[1] / "raw" / "sec" / "nvda-10k-2026-02-25.json"
    raw = json.loads(raw_path.read_text())

    facts, edges = leg_xbrl.extract(raw)

    rev_facts = [f for f in facts if f["metric"] == "revenue"]
    assert len(rev_facts) == 1, f"Expected 1 revenue fact, got {len(rev_facts)}"
    assert rev_facts[0]["value"] > 200_000_000_000, (
        f"Revenue {rev_facts[0]['value']} unexpectedly low"
    )

    seg_edges = [e for e in edges if e["predicate"] == "IN_SEGMENT"]
    assert len(seg_edges) == 2, f"Expected exactly 2 IN_SEGMENT edges, got {len(seg_edges)}"

    # Verify edge shape
    for e in seg_edges:
        for key in ("subject", "subject_type", "predicate", "target", "target_type",
                    "as_of", "source", "from_structured", "extractor", "evidence"):
            assert key in e, f"Missing key {key!r} in edge {e}"
