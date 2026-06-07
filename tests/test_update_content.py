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
