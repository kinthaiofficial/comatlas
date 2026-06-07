"""Unit tests for eval/run_eval.py: AC-1, AC-2, AC-4 metric functions."""
import sys
from pathlib import Path

# Ensure eval/ module is importable
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from eval.run_eval import ac1_precision_high, ac2_source_coverage, ac4_alias_accuracy


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

GOLD = {
    "triples": [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "samsung"},
        {"subject": "nvidia-compute-networking", "predicate": "IN_SEGMENT", "target": "nvidia"},
        {"subject": "nvidia-graphics", "predicate": "IN_SEGMENT", "target": "nvidia"},
    ]
}

ALIAS_CASES = [
    {"surface": "TSMC", "id": "tsmc"},
    {"surface": "Taiwan Semiconductor Manufacturing Company", "id": "tsmc"},
    {"surface": "Samsung", "id": "samsung"},
    {"surface": "NVIDIA Corporation", "id": "nvidia"},
    {"surface": "AMD", "id": "amd"},
]


# ---------------------------------------------------------------------------
# AC-1: high-edge precision (scoped to gold subject-predicate pairs)
# ---------------------------------------------------------------------------

def test_ac1_all_correct():
    """All high edges that fall within the gold scope are correct -> precision 1.0."""
    edges = [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "high"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "samsung", "confidence": "high"},
        {"subject": "nvidia-compute-networking", "predicate": "IN_SEGMENT", "target": "nvidia", "confidence": "high"},
    ]
    assert ac1_precision_high(edges, GOLD) == 1.0


def test_ac1_one_wrong():
    """One high edge has wrong target -> precision = 2/3."""
    edges = [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "high"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "samsung", "confidence": "high"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "intel", "confidence": "high"},  # wrong
    ]
    result = ac1_precision_high(edges, GOLD)
    assert abs(result - 2/3) < 1e-9


def test_ac1_out_of_scope_high_edge_not_judged():
    """A high edge whose (subject, predicate) is NOT in gold scope must not lower precision."""
    edges = [
        # In-scope and correct
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "high"},
        # Out-of-scope (nvidia, COMPETES_WITH) is not in gold -> must be ignored
        {"subject": "nvidia", "predicate": "COMPETES_WITH", "target": "amd", "confidence": "high"},
        {"subject": "nvidia", "predicate": "COMPETES_WITH", "target": "garbage", "confidence": "high"},
    ]
    result = ac1_precision_high(edges, GOLD)
    assert result == 1.0, f"Expected 1.0, got {result}"


def test_ac1_medium_edges_not_judged():
    """Medium-confidence edges are excluded even if they match the gold scope."""
    edges = [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "medium"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "wrong", "confidence": "medium"},
    ]
    # No high edges in scope -> returns 1.0 (vacuously true)
    assert ac1_precision_high(edges, GOLD) == 1.0


def test_ac1_no_high_edges():
    """No high edges at all -> vacuously 1.0."""
    edges = [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "medium"},
    ]
    assert ac1_precision_high(edges, GOLD) == 1.0


def test_ac1_empty_edges():
    """Empty edge list -> 1.0."""
    assert ac1_precision_high([], GOLD) == 1.0


def test_ac1_perfect_score_all_in_scope():
    """All high edges are in scope and correct -> 1.0."""
    edges = [
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc", "confidence": "high"},
        {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "samsung", "confidence": "high"},
        {"subject": "nvidia-compute-networking", "predicate": "IN_SEGMENT", "target": "nvidia", "confidence": "high"},
        {"subject": "nvidia-graphics", "predicate": "IN_SEGMENT", "target": "nvidia", "confidence": "high"},
    ]
    assert ac1_precision_high(edges, GOLD) == 1.0


# ---------------------------------------------------------------------------
# AC-2: source coverage
# ---------------------------------------------------------------------------

def test_ac2_all_sourced():
    edges = [
        {"has_source": True},
        {"has_source": True},
        {"has_source": True},
    ]
    assert ac2_source_coverage(edges) == 1.0


def test_ac2_none_sourced():
    edges = [{"has_source": False}, {"has_source": False}]
    assert ac2_source_coverage(edges) == 0.0


def test_ac2_mixed():
    edges = [{"has_source": True}, {"has_source": False}, {"has_source": True}, {"has_source": True}]
    assert abs(ac2_source_coverage(edges) - 0.75) < 1e-9


def test_ac2_empty():
    """Empty edge list -> 1.0 (vacuous)."""
    assert ac2_source_coverage([]) == 1.0


# ---------------------------------------------------------------------------
# AC-4: alias accuracy
# ---------------------------------------------------------------------------

def test_ac4_all_correct():
    assert ac4_alias_accuracy(ALIAS_CASES) == 1.0


def test_ac4_one_wrong(monkeypatch):
    """If one case returns wrong id, accuracy drops."""
    import eval.run_eval as eval_module
    original = eval_module.normalize_surface

    def patched(surface, alias_map=None):
        if surface == "AMD":
            return ("wrong-id", True)
        return original(surface, alias_map)

    # Patch the name as used inside eval/run_eval.py
    monkeypatch.setattr(eval_module, "normalize_surface", patched)
    result = eval_module.ac4_alias_accuracy(ALIAS_CASES)
    assert abs(result - 4/5) < 1e-9


def test_ac4_empty():
    """Empty case list -> 1.0 (vacuous)."""
    assert ac4_alias_accuracy([]) == 1.0


def test_ac4_tsmc_full_form():
    """Full legal name resolves to tsmc."""
    cases = [{"surface": "Taiwan Semiconductor Manufacturing Company Limited", "id": "tsmc"}]
    assert ac4_alias_accuracy(cases) == 1.0


def test_ac4_chinese_form():
    """Chinese alias resolves correctly."""
    cases = [{"surface": "台积电", "id": "tsmc"}, {"surface": "英伟达", "id": "nvidia"}]
    assert ac4_alias_accuracy(cases) == 1.0
