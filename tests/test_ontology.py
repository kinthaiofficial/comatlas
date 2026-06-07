from scripts.ontology import load_entity_types, load_predicates, load_alias_map

def test_entity_types_closed_set():
    types = load_entity_types()
    assert types == {"Company", "Product", "Chip", "Fab", "DataCenter", "Technology", "Person", "Segment"}

def test_predicates_have_domain_range():
    preds = load_predicates()
    assert "HEADQUARTERED_IN" not in preds            # G9: reserved/disabled
    for name, spec in preds.items():
        assert spec["domain"] and spec["range"], name

def test_alias_map_inverted_casefold():
    amap = load_alias_map()
    assert amap["nvda"] == "nvidia"
    assert amap["台积电"] == "tsmc"
    assert amap["nvidia"] == "nvidia"                  # canonical id maps to itself
