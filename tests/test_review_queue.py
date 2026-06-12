from scripts import review_queue as rq

ITEM = {"kind": "low", "subject": "nvidia", "predicate": "IN_SEGMENT",
        "candidates": [{"target": "data-center", "extractors": ["claude"], "sources": ["s1"],
                        "evidence": [{"source": "s1", "text": "edge computing is mentioned"}]}]}


def test_appends_item_with_details(tmp_path):
    p = tmp_path / "review_queue.md"
    rq.append_items(p, [ITEM], today="2026-06-12")
    body = p.read_text()
    assert "nvidia" in body and "IN_SEGMENT" in body and "data-center" in body and "claude" in body


def test_idempotent_no_duplicate(tmp_path):
    p = tmp_path / "review_queue.md"
    rq.append_items(p, [ITEM], today="2026-06-12")
    rq.append_items(p, [ITEM], today="2026-06-13")          # same item again, later day
    assert p.read_text().count("<!-- RQ:low:nvidia:IN_SEGMENT:data-center -->") == 1   # one block


def test_distinct_items_both_appended(tmp_path):
    p = tmp_path / "review_queue.md"
    other = {**ITEM, "candidates": [{"target": "edge-computing", "extractors": ["claude"],
                                     "sources": ["s1"], "evidence": []}]}
    rq.append_items(p, [ITEM, other], today="2026-06-12")
    body = p.read_text()
    assert "data-center" in body and "edge-computing" in body


def test_empty_items_no_crash_no_entries(tmp_path):
    p = tmp_path / "review_queue.md"
    rq.append_items(p, [], today="2026-06-12")
    assert not p.exists() or "data-center" not in p.read_text()
