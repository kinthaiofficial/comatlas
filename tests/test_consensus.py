from scripts.consensus import merge_votes, score, score_m1


def edge(subj="nvidia", pred="MANUFACTURED_BY", tgt="tsmc", src="s1", extractor="claude",
         structured=False, stype="Company"):
    return {"subject": subj, "predicate": pred, "target": tgt, "source": src,
            "extractors": [extractor], "evidence": "NVIDIA relies on TSMC.", "as_of": "2026-Q1",
            "subject_type": stype, "target_type": "Fab", "from_structured": structured}


KEY = ("nvidia", "MANUFACTURED_BY", "tsmc")


def test_m1_scorer_still_present():
    assert score_m1(edge()) == "medium" and score_m1(edge(structured=True)) == "high"


def test_two_votes_two_sources_is_high():
    by = merge_votes([edge(src="s1"), edge(src="s2", extractor="minimax")])
    assert score(by[KEY], grounding_ok=True) == "high"          # agree>=2 and corro>=2


def test_two_votes_one_source_is_medium():
    by = merge_votes([edge(), edge(extractor="minimax")])        # both src=s1
    assert score(by[KEY], True) == "medium"


def test_single_vote_grounded_is_medium():
    by = merge_votes([edge()])
    assert score(by[KEY], True) == "medium"


def test_grounding_failure_is_low():
    by = merge_votes([edge(src="s1"), edge(extractor="minimax", src="s2")])
    assert score(by[KEY], grounding_ok=False) == "low"          # grounding gate overrides votes


def test_structured_bypasses_voting_and_grounding():
    by = merge_votes([edge(extractor="xbrl", structured=True)])
    assert score(by[KEY], grounding_ok=False) == "high"         # structured trusted, no grounding


def test_human_vote_counts_and_is_preserved():
    by = merge_votes([edge(extractor="human", src="s1"), edge(extractor="claude", src="s2")])
    rec = by[KEY]
    assert "human" in rec["extractors"] and "claude" in rec["extractors"]   # red line #8: never relabeled
    assert score(rec, True) == "high"                          # human + claude, 2 sources


def test_weak_model_silence_never_demotes():
    # claude+minimax agree (1 source) -> medium; a silent glirel must not change that
    by = merge_votes([edge(), edge(extractor="minimax")])
    assert score(by[KEY], True) == "medium"


# ── M2b: functional-conflict detection (G12) ─────────────────────────────────
from scripts.consensus import find_conflicts


def test_subsidiary_of_is_always_functional_conflict():
    by = merge_votes([
        edge(subj="mellanox", pred="SUBSIDIARY_OF", tgt="nvidia", stype="Company"),
        edge(subj="mellanox", pred="SUBSIDIARY_OF", tgt="intel", extractor="minimax", stype="Company")])
    conflicts = find_conflicts(by)
    assert len(conflicts) == 1 and conflicts[0]["subject"] == "mellanox"
    assert {c["target"] for c in conflicts[0]["candidates"]} == {"nvidia", "intel"}


def test_manufactured_by_company_subject_is_not_conflict():
    by = merge_votes([
        edge(subj="nvidia", pred="MANUFACTURED_BY", tgt="tsmc", stype="Company"),
        edge(subj="nvidia", pred="MANUFACTURED_BY", tgt="samsung", stype="Company")])
    assert find_conflicts(by) == []           # a company can use multiple foundries


def test_manufactured_by_chip_subject_is_conflict():
    by = merge_votes([
        edge(subj="h100", pred="MANUFACTURED_BY", tgt="tsmc", stype="Chip"),
        edge(subj="h100", pred="MANUFACTURED_BY", tgt="samsung", extractor="minimax", stype="Chip")])
    assert len(find_conflicts(by)) == 1       # one chip is single-foundry (G12)


def test_non_functional_predicate_never_conflicts():
    by = merge_votes([edge(subj="nvidia", pred="COMPETES_WITH", tgt="amd"),
                      edge(subj="nvidia", pred="COMPETES_WITH", tgt="intel")])
    assert find_conflicts(by) == []           # competes_with is multi-valued
