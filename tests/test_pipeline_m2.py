"""M2a pipeline: second vote + grounding + scoring + review queue."""
import json
import frontmatter
from scripts import extract_consensus as pipe

RAW = {"source_id": "nvda-10k-2026-02-26", "form": "10-K", "url": "https://x",
       "accession": "0001-26-1", "filing_date": "2026-02-26", "as_of": "2026-Q1",
       "sections": {"Item 1": "NVIDIA relies on TSMC to manufacture its GPUs."}}

def _triple(extractor):
    return {"subject": "NVIDIA", "subject_type": "Company", "predicate": "MANUFACTURED_BY",
            "object": "TSMC", "object_type": "Fab", "evidence": "NVIDIA relies on TSMC to manufacture its GPUs.",
            "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": extractor}

XBRL_EDGE = {"subject": "nvidia-compute-networking", "subject_type": "Segment", "target": "nvidia",
             "target_type": "Company", "predicate": "IN_SEGMENT", "as_of": "2026-Q1",
             "source": "nvda-10k-2026-02-26", "extractor": "xbrl", "from_structured": True}


def _setup(tmp_path, monkeypatch, claude, minimax, grounding_ok=True, xbrl=([], [])):
    raw_dir = tmp_path / "raw" / "sec"; raw_dir.mkdir(parents=True)
    raw_dir.joinpath("nvda-10k-2026-02-26.json").write_text(json.dumps(RAW))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps(
        {"nvda-10k-2026-02-26": {"accession": "0001-26-1", "processed": False}}))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe, "ROOT", tmp_path)
    monkeypatch.setattr(pipe.anchor_claude, "extract_source",
                        lambda raw, runner=None, checkpoint_dir=None: claude)
    monkeypatch.setattr(pipe.second_minimax, "extract_source", lambda raw: minimax)
    monkeypatch.setattr(pipe.leg_xbrl, "extract", lambda raw: xbrl)
    monkeypatch.setattr(pipe.grounding, "grounding_ok", lambda *a, **k: grounding_ok)


def _rel(tmp_path, target="tsmc"):
    nv = frontmatter.load(tmp_path / "content" / "entities" / "nvidia.md")
    return next((r for r in nv["relations"] if r["target"] == target), None)


def test_two_models_agree_unions_extractors_medium(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [_triple("claude")], [_triple("minimax")])
    pipe.run(today="2026-06-12")
    r = _rel(tmp_path)
    assert set(r["extractors"]) == {"claude", "minimax"}     # both votes recorded
    assert r["confidence"] == "medium"                       # 2 votes but 1 source (spec §5.2)


def test_grounding_failure_is_low_and_queued(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [_triple("claude")], [], grounding_ok=False)
    pipe.run(today="2026-06-12")
    assert _rel(tmp_path)["confidence"] == "low"
    auto = (tmp_path / "content" / "entities" / "nvidia.md").read_text() \
        .split("AUTO-RELATIONS:BEGIN")[1].split("AUTO-RELATIONS:END")[0]
    assert "tsmc" not in auto                                # red line #3: low never rendered
    rq = (tmp_path / "review_queue.md").read_text()
    assert "MANUFACTURED_BY" in rq and "tsmc" in rq          # surfaced for human review


def test_structured_edge_is_high_bypassing_grounding(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [], [], grounding_ok=False, xbrl=([], [XBRL_EDGE]))
    pipe.run(today="2026-06-12")
    seg = frontmatter.load(tmp_path / "content" / "entities" / "nvidia-compute-networking.md")
    r = next(r for r in seg["relations"] if r["predicate"] == "IN_SEGMENT")
    assert r["confidence"] == "high"                         # structured trusted despite grounding=False


def test_human_gold_plus_claude_unions_provenance(tmp_path, monkeypatch):
    # first run seeds a human gold edge; second run re-extracts via claude -> union, no relabel
    _setup(tmp_path, monkeypatch, [{**_triple("human")}], [])
    pipe.run(today="2026-06-12")
    (tmp_path / "raw" / "_state.json").write_text(json.dumps(
        {"nvda-10k-2026-02-26": {"accession": "0001-26-1", "processed": False}}))
    monkeypatch.setattr(pipe.anchor_claude, "extract_source",
                        lambda raw, runner=None, checkpoint_dir=None: [_triple("claude")])
    pipe.run(today="2026-06-13")
    assert set(_rel(tmp_path)["extractors"]) == {"claude", "human"}   # union, human preserved (#8)


def test_minimax_only_edge_queued_not_published(tmp_path, monkeypatch):
    mm_only = {"subject": "NVIDIA", "subject_type": "Company", "predicate": "PARTNER_WITH",
               "object": "Acme Corp", "object_type": "Company", "evidence": "Acme partners with NVIDIA.",
               "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": "minimax"}
    _setup(tmp_path, monkeypatch, [], [mm_only])
    pipe.run(today="2026-06-12")
    assert not (tmp_path / "content" / "entities" / "acme-corp.md").exists()   # no junk entity page
    rq = (tmp_path / "review_queue.md").read_text()
    assert "weak-only" in rq and "PARTNER_WITH" in rq                          # surfaced, not published


def test_human_edge_published_despite_grounding_false(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [_triple("human")], [], grounding_ok=False)
    pipe.run(today="2026-06-12")
    r = _rel(tmp_path)
    assert r is not None and r["confidence"] != "low"    # human authoritative — grounding bypassed
    assert "human" in r["extractors"]


def test_functional_conflict_routed_to_queue_not_published(tmp_path, monkeypatch):
    claude = [{"subject": "Mellanox", "subject_type": "Company", "predicate": "SUBSIDIARY_OF",
               "object": "NVIDIA", "object_type": "Company", "evidence": "Mellanox is part of NVIDIA.",
               "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": "claude"}]
    minimax = [{"subject": "Mellanox", "subject_type": "Company", "predicate": "SUBSIDIARY_OF",
                "object": "Intel", "object_type": "Company", "evidence": "Mellanox belongs to Intel.",
                "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": "minimax"}]
    _setup(tmp_path, monkeypatch, claude, minimax)
    pipe.run(today="2026-06-12")
    mp = tmp_path / "content" / "entities" / "mellanox.md"
    if mp.exists():
        rels = frontmatter.load(mp).metadata.get("relations") or []
        assert not any(r["predicate"] == "SUBSIDIARY_OF" for r in rels)   # conflicting edge not published
    rq = (tmp_path / "review_queue.md").read_text()
    assert "conflict" in rq and "SUBSIDIARY_OF" in rq                     # surfaced for human arbitration


def _seed_entity(tmp_path, eid):
    d = tmp_path / "content" / "entities"; d.mkdir(parents=True, exist_ok=True)
    (d / f"{eid}.md").write_text(
        f"---\ntype: Company\nid: {eid}\nlabel: {eid}\naliases: [{eid}]\nconfidence: medium\n"
        f"publish: true\nlast_updated: '2026-06-13'\nsources: []\nrelations: []\n---\n"
        "<!-- AUTO-RELATIONS:BEGIN -->\n<!-- AUTO-RELATIONS:END -->\n")


def test_wikidata_corroborates_existing_entities_only(tmp_path, monkeypatch):
    _seed_entity(tmp_path, "mellanox"); _seed_entity(tmp_path, "nvidia")
    wiki = [{"subject": "Mellanox", "subject_type": "Company", "object": "NVIDIA", "object_type": "Company",
             "predicate": "SUBSIDIARY_OF", "as_of": "2026-Q1", "evidence": "Wikidata P355",
             "source": "wikidata-q182477", "extractor": "wikidata", "from_structured": True},
            {"subject": "Obscure Sub", "subject_type": "Company", "object": "NVIDIA", "object_type": "Company",
             "predicate": "SUBSIDIARY_OF", "as_of": "2026-Q1", "evidence": "Wikidata P355",
             "source": "wikidata-q182477", "extractor": "wikidata", "from_structured": True}]
    _setup(tmp_path, monkeypatch, [], [])
    monkeypatch.setattr(pipe.leg_wikidata, "extract", lambda as_of="2026-Q1": wiki)
    pipe.run(today="2026-06-13")
    mel = frontmatter.load(tmp_path / "content" / "entities" / "mellanox.md")
    subs = [r for r in mel.metadata.get("relations") or [] if r["predicate"] == "SUBSIDIARY_OF"]
    assert any(r["target"] == "nvidia" and r["confidence"] == "high" for r in subs)   # structured -> high
    assert any("wikidata" in r["extractors"] for r in subs)
    assert not (tmp_path / "content" / "entities" / "obscure-sub.md").exists()         # new entity filtered out


def test_wikidata_outage_is_tolerated(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [_triple("claude")], [])
    def _boom(as_of="2026-Q1"): raise RuntimeError("429 rate limited")
    monkeypatch.setattr(pipe.leg_wikidata, "extract", _boom)
    assert pipe.run(today="2026-06-13") == ["nvda-10k-2026-02-26"]      # WDQS down doesn't break the run
