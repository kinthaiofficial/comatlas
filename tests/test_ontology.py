from scripts.ontology import load_entity_types, load_predicates, load_alias_map, edge_satisfies_ontology

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


# --- edge_satisfies_ontology tests ---

def _preds():
    return load_predicates()


def test_edge_satisfies_ontology_technology_in_segment_false():
    """Technology is NOT in IN_SEGMENT domain → must be rejected."""
    preds = _preds()
    ok, reason = edge_satisfies_ontology(
        {"predicate": "IN_SEGMENT", "subject_type": "Technology", "target_type": "Segment"},
        preds,
    )
    assert not ok
    assert "Technology" in reason


def test_edge_satisfies_ontology_product_in_segment_true():
    """Product IS in IN_SEGMENT domain, Company IS in range → must be accepted."""
    preds = _preds()
    ok, reason = edge_satisfies_ontology(
        {"predicate": "IN_SEGMENT", "subject_type": "Product", "target_type": "Company"},
        preds,
    )
    assert ok, reason


def test_edge_satisfies_ontology_company_supplies_company_true():
    """Company SUPPLIES Company → valid (Company in domain, Company in range)."""
    preds = _preds()
    ok, reason = edge_satisfies_ontology(
        {"predicate": "SUPPLIES", "subject_type": "Company", "target_type": "Company"},
        preds,
    )
    assert ok, reason


def test_edge_satisfies_ontology_person_supplies_company_false():
    """Person SUPPLIES Company → invalid (Person not in SUPPLIES domain)."""
    preds = _preds()
    ok, reason = edge_satisfies_ontology(
        {"predicate": "SUPPLIES", "subject_type": "Person", "target_type": "Company"},
        preds,
    )
    assert not ok
    assert "Person" in reason


def test_edge_satisfies_ontology_unknown_predicate_false():
    """Unknown predicate → always rejected."""
    preds = _preds()
    ok, reason = edge_satisfies_ontology(
        {"predicate": "UNKNOWN_PRED", "subject_type": "Company", "target_type": "Company"},
        preds,
    )
    assert not ok
    assert "UNKNOWN_PRED" in reason


def test_edge_satisfies_ontology_defaults_to_loaded_predicates():
    """When predicates not supplied, function loads them itself."""
    ok, _ = edge_satisfies_ontology(
        {"predicate": "COMPETES_WITH", "subject_type": "Company", "target_type": "Company"}
    )
    assert ok
