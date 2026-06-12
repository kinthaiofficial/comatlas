from scripts.quote import short_quote


def test_clips_to_max_words_around_focus():
    ev = ("We utilize foundries, such as Taiwan Semiconductor Manufacturing Company Limited, or TSMC, "
          "and Samsung Electronics Co., Ltd., or Samsung, to produce our semiconductor wafers.")
    q = short_quote(ev, "TSMC", max_words=15)
    quoted_words = [w for w in q.split() if w != "…"]      # ellipsis is a trim marker, not a quoted word
    assert len(quoted_words) <= 15
    assert "TSMC" in q
    assert "…" in q                                        # trimmed -> ellipsis marker


def test_short_evidence_returned_verbatim_without_ellipsis():
    ev = "We purchase memory from SK Hynix Inc., Micron Technology, Inc., and Samsung."
    q = short_quote(ev, "Micron Technology, Inc.", max_words=15)
    assert q == ev                                         # <=15 words: returned as-is
    assert "…" not in q


def test_focus_absent_falls_back_to_head():
    ev = "A B C D E F G H I J K L M N O P Q R"
    q = short_quote(ev, "ZZZ", max_words=5)
    assert q.startswith("A B C D E") and q.endswith("…")


def test_empty_evidence_returns_empty():
    assert short_quote("", "TSMC") == ""
