import frontmatter
from scripts import update_content as uc

EDGE = {"subject": "nvidia", "subject_type": "Company", "predicate": "MANUFACTURED_BY",
        "target": "tsmc", "target_type": "Fab", "as_of": "2026-Q1",
        "source": "src-1", "confidence": "medium", "extractors": ["claude"],
        "evidence": "NVIDIA relies on TSMC."}
SRC = {"id": "src-1", "kind": "sec-filing", "title": "10-K", "url": "https://x", "date": "2026-02-26"}

def test_creates_subject_target_and_source_pages(tmp_path):
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")
    nv = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert nv["relations"][0]["target"] == "tsmc" and nv["relations"][0]["source"] == "src-1"
    assert (tmp_path / "entities" / "tsmc.md").exists()
    assert (tmp_path / "sources" / "src-1.md").exists()
    assert nv["publish"] is True and nv["last_updated"] == "2026-06-07"

def test_merge_same_edge_updates_asof_and_corroborates(tmp_path):
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")
    e2 = {**EDGE, "as_of": "2026-Q2", "source": "src-2", "extractors": ["claude"]}
    uc.apply(tmp_path, edges=[e2], facts=[], source_meta={**SRC, "id": "src-2"}, today="2026-06-08")
    nv = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert len(nv["relations"]) == 1
    r = nv["relations"][0]
    assert r["as_of"] == "2026-Q2" and r["source"] == "src-1" and r["corroborates"] == ["src-2"]

def test_low_edge_not_rendered_in_body(tmp_path):
    uc.apply(tmp_path, edges=[{**EDGE, "confidence": "low"}], facts=[], source_meta=SRC, today="2026-06-07")
    body = (tmp_path / "entities" / "nvidia.md").read_text()
    assert "tsmc" not in body.split("AUTO-RELATIONS:BEGIN")[1].split("AUTO-RELATIONS:END")[0]

def test_handwritten_prose_preserved(tmp_path):
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")
    p = tmp_path / "entities" / "nvidia.md"
    p.write_text(p.read_text().replace("<!-- AUTO-RELATIONS:BEGIN -->",
                 "Hand-written intro.\n\n<!-- AUTO-RELATIONS:BEGIN -->"))
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-08")
    assert "Hand-written intro." in p.read_text()

def test_output_passes_linter(tmp_path):
    from scripts.lint_frontmatter import lint_dir
    uc.apply(tmp_path, edges=[EDGE], facts=[{"entity": "nvidia", "metric": "revenue",
        "value": 215_938_000_000, "unit": "USD", "period": "FY2026", "source": "src-1",
        "confidence": "high", "extractors": ["xbrl"]}], source_meta=SRC, today="2026-06-07")
    assert lint_dir(tmp_path) == []

def test_facts_replace_same_metric_period(tmp_path):
    f = {"entity": "nvidia", "metric": "revenue", "value": 1, "unit": "USD", "period": "FY2026",
         "source": "src-1", "confidence": "high", "extractors": ["xbrl"]}
    uc.apply(tmp_path, edges=[], facts=[f], source_meta=SRC, today="2026-06-07")
    uc.apply(tmp_path, edges=[], facts=[{**f, "value": 2}], source_meta=SRC, today="2026-06-08")
    nv = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert len(nv["facts"]) == 1 and nv["facts"][0]["value"] == 2


def test_confidence_raise_only(tmp_path):
    """apply high then medium → stays high; medium then high → becomes high."""
    e_high = {**EDGE, "confidence": "high"}
    e_medium = {**EDGE, "confidence": "medium"}

    # Apply high first, then medium → should stay high
    uc.apply(tmp_path, edges=[e_high], facts=[], source_meta=SRC, today="2026-06-07")
    uc.apply(tmp_path, edges=[e_medium], facts=[], source_meta={**SRC, "id": "src-2"},
             today="2026-06-07")
    nv = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert nv["relations"][0]["confidence"] == "high"

    # Fresh dir: apply medium first, then high → should become high
    tmp2 = tmp_path / "sub"
    tmp2.mkdir()
    uc.apply(tmp2, edges=[e_medium], facts=[], source_meta=SRC, today="2026-06-07")
    uc.apply(tmp2, edges=[e_high], facts=[], source_meta={**SRC, "id": "src-2"},
             today="2026-06-07")
    nv2 = frontmatter.load(tmp2 / "entities" / "nvidia.md")
    assert nv2["relations"][0]["confidence"] == "high"


def test_low_page_not_published(tmp_path):
    """Pre-create entity page with low confidence (publish: false); apply edge → publish stays False; lint passes."""
    from scripts.lint_frontmatter import lint_dir
    import frontmatter as fm

    # Pre-create nvidia page with low confidence and publish: false
    entities_dir = tmp_path / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)
    nv_post = fm.Post(f"{uc.AUTO_BEGIN}\n{uc.AUTO_END}\n")
    nv_post.metadata = {
        "type": "Company",
        "id": "nvidia",
        "label": "NVIDIA",
        "aliases": ["NVIDIA"],
        "confidence": "low",
        "publish": False,
        "last_updated": "2026-06-07",
        "sources": [],
        "relations": [],
    }
    (entities_dir / "nvidia.md").write_text(fm.dumps(nv_post) + "\n")

    # Apply an edge that touches nvidia
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")

    nv = fm.load(tmp_path / "entities" / "nvidia.md")
    assert nv["publish"] is False
    assert lint_dir(tmp_path) == []


def test_byte_idempotent(tmp_path):
    """apply twice with identical inputs → file bytes identical between run 1 and run 2."""
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")
    bytes_after_first = (tmp_path / "entities" / "nvidia.md").read_bytes()

    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")
    bytes_after_second = (tmp_path / "entities" / "nvidia.md").read_bytes()

    assert bytes_after_first == bytes_after_second


def test_malformed_auto_block_raises(tmp_path):
    """Page body with END before BEGIN → ValueError raised."""
    import pytest
    import frontmatter as fm

    # Create a page where AUTO_END comes before AUTO_BEGIN
    entities_dir = tmp_path / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)
    bad_post = fm.Post(f"{uc.AUTO_END}\nsome text\n{uc.AUTO_BEGIN}\n")
    bad_post.metadata = {
        "type": "Company",
        "id": "nvidia",
        "label": "NVIDIA",
        "aliases": ["NVIDIA"],
        "confidence": "medium",
        "publish": True,
        "last_updated": "2026-06-07",
        "sources": [],
        "relations": [],
    }
    (entities_dir / "nvidia.md").write_text(fm.dumps(bad_post) + "\n")

    with pytest.raises(ValueError, match="nvidia"):
        uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-07")


# ── M2.5 Wiki: evidence short-quote ──────────────────────────────────────────
LONG_EV = ("We utilize foundries, such as Taiwan Semiconductor Manufacturing Company Limited, or TSMC, "
           "and Samsung Electronics Co., Ltd., or Samsung, to produce our semiconductor wafers.")
QEDGE = {**EDGE, "target_label": "TSMC", "evidence": LONG_EV}

def test_edge_persists_short_quote(tmp_path):
    uc.apply(tmp_path, edges=[QEDGE], facts=[], source_meta=SRC, today="2026-06-12")
    r = next(r for r in frontmatter.load(tmp_path / "entities" / "nvidia.md")["relations"]
             if r["target"] == "tsmc")
    quoted = [w for w in r["quote"].split() if w != "…"]
    assert len(quoted) <= 15 and "TSMC" in r["quote"]

def test_auto_block_renders_basis_column(tmp_path):
    uc.apply(tmp_path, edges=[QEDGE], facts=[], source_meta=SRC, today="2026-06-12")
    auto = (tmp_path / "entities" / "nvidia.md").read_text().split("AUTO-RELATIONS:BEGIN")[1]
    assert "basis" in auto and "TSMC" in auto


# ── M2.5 Wiki: managed SUMMARY block ─────────────────────────────────────────
def test_summary_block_rendered_and_flagged(tmp_path):
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-12",
             summaries={"nvidia": "NVIDIA designs accelerated computing platforms."})
    post = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert post.metadata.get("summary_by") == "claude"
    assert "SUMMARY:BEGIN" in post.content and "accelerated computing platforms" in post.content
    assert post.content.index("SUMMARY:BEGIN") < post.content.index("AUTO-RELATIONS:BEGIN")

def test_summary_only_entity_without_edges(tmp_path):
    uc.apply(tmp_path, edges=[], facts=[], source_meta=SRC, today="2026-06-12",
             summaries={"nvidia": "Standalone summary."})
    post = frontmatter.load(tmp_path / "entities" / "nvidia.md")
    assert "Standalone summary." in post.content and post.metadata.get("summary_by") == "claude"

def test_handwritten_prose_between_blocks_preserved(tmp_path):
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-12",
             summaries={"nvidia": "First summary."})
    p = tmp_path / "entities" / "nvidia.md"
    post = frontmatter.load(p)
    post.content = post.content.replace("<!-- SUMMARY:END -->",
                                        "<!-- SUMMARY:END -->\n\nHUMAN NOTE: verify Groq deal.", 1)
    p.write_text(frontmatter.dumps(post) + "\n")
    uc.apply(tmp_path, edges=[EDGE], facts=[], source_meta=SRC, today="2026-06-13",
             summaries={"nvidia": "Second summary."})
    final = (tmp_path / "entities" / "nvidia.md").read_text()
    assert "HUMAN NOTE: verify Groq deal." in final
    assert "Second summary." in final and "First summary." not in final


# ── M2.5 Wiki: clickable source (new tab) + basis deep-link (text fragment) ───
def test_source_external_newtab_and_basis_deeplink(tmp_path):
    uc.apply(tmp_path, edges=[QEDGE], facts=[], source_meta=SRC, today="2026-06-12")
    auto = (tmp_path / "entities" / "nvidia.md").read_text().split("AUTO-RELATIONS:BEGIN")[1]
    assert 'target="_blank"' in auto and 'rel="noopener"' in auto
    assert 'href="https://x"' in auto          # source cell -> external SEC url
    assert "#:~:text=" in auto                  # basis cell -> text-fragment deep link
    assert "[[sources/" not in auto             # broken table-pipe wikilink is gone
