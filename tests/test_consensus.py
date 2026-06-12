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
