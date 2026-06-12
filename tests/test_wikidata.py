import pytest
from scripts.extract import leg_wikidata as wd

BINDINGS = [
    {"prop": {"value": "http://www.wikidata.org/prop/direct/P355"}, "label": {"value": "Mellanox Technologies"}},
    {"prop": {"value": "http://www.wikidata.org/prop/direct/P1830"}, "label": {"value": "Arm Holdings"}},
    {"prop": {"value": "http://www.wikidata.org/prop/direct/P999"}, "label": {"value": "Ignored Prop"}},
]


def test_subsidiary_orientation_incoming():
    edges = wd.to_edges(BINDINGS, "NVIDIA", "2026-Q1")
    sub = next(e for e in edges if e["predicate"] == "SUBSIDIARY_OF")
    assert sub["subject"] == "Mellanox Technologies" and sub["object"] == "NVIDIA"   # X SUBSIDIARY_OF filer
    assert sub["extractor"] == "wikidata" and sub["from_structured"] is True


def test_owns_stake_orientation_outgoing():
    edges = wd.to_edges(BINDINGS, "NVIDIA", "2026-Q1")
    own = next(e for e in edges if e["predicate"] == "OWNS_STAKE_IN")
    assert own["subject"] == "NVIDIA" and own["object"] == "Arm Holdings"            # filer OWNS_STAKE_IN X


def test_unknown_property_dropped():
    edges = wd.to_edges(BINDINGS, "NVIDIA", "2026-Q1")
    assert len(edges) == 2 and all(e["source"] == "wikidata-q182477" for e in edges)


@pytest.mark.live
def test_live_wikidata_returns_mellanox_subsidiary():
    edges = wd.extract()
    assert any(e["predicate"] == "SUBSIDIARY_OF" and "Mellanox" in e["subject"] for e in edges)
