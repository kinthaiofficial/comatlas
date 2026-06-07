"""Tests for M1 pipeline entry: extract_consensus.py + consensus.py."""
import json
import pytest
from scripts import extract_consensus as pipe
from scripts.lint_frontmatter import lint_dir

RAW = {"source_id": "nvda-10k-2026-02-26", "form": "10-K", "url": "https://x",
       "accession": "0001-26-1", "filing_date": "2026-02-26", "as_of": "2026-Q1",
       "sections": {"Item 1": "NVIDIA relies on TSMC. NVIDIA competes with AMD."}}
TRIPLES = [
    {"subject": "NVIDIA", "subject_type": "Company", "predicate": "MANUFACTURED_BY",
     "object": "TSMC", "object_type": "Fab", "evidence": "NVIDIA relies on TSMC.",
     "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": "claude"},
    {"subject": "NVIDIA", "subject_type": "Company", "predicate": "COMPETES_WITH",
     "object": "Advanced Micro Devices", "object_type": "Company",
     "evidence": "NVIDIA competes with AMD.", "as_of": "2026-Q1",
     "source": "nvda-10k-2026-02-26", "extractor": "claude"}]


def _setup(tmp_path, monkeypatch):
    """Write raw fixture files and monkeypatch path + extractors."""
    raw_dir = tmp_path / "raw" / "sec"
    raw_dir.mkdir(parents=True)
    raw_dir.joinpath("nvda-10k-2026-02-26.json").write_text(json.dumps(RAW))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps(
        {"nvda-10k-2026-02-26": {"accession": "0001-26-1", "processed": False}}))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe.anchor_claude, "extract_source", lambda raw, runner=None: TRIPLES)
    monkeypatch.setattr(pipe.leg_xbrl, "extract", lambda raw: ([], []))


def test_m1_end_to_end(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    done = pipe.run(today="2026-06-07")
    assert done == ["nvda-10k-2026-02-26"]

    import frontmatter
    nv = frontmatter.load(tmp_path / "content" / "entities" / "nvidia.md")
    rels = {(r["predicate"], r["target"]): r for r in nv["relations"]}
    assert rels[("MANUFACTURED_BY", "tsmc")]["confidence"] == "medium"   # 1 vote, M1
    assert ("COMPETES_WITH", "amd") in rels                              # alias resolved

    state = json.loads((tmp_path / "raw" / "_state.json").read_text())
    assert state["nvda-10k-2026-02-26"]["processed"] is True
    assert pipe.run(today="2026-06-08") == []                            # incremental


def test_m1_output_passes_linter(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    pipe.run(today="2026-06-07")

    from scripts.lint_frontmatter import lint_dir
    errors = lint_dir(tmp_path / "content")
    assert errors == [], f"Lint errors: {errors}"


def test_xbrl_skipped_for_8k(tmp_path, monkeypatch):
    """8-K must not call leg_xbrl.extract; pipeline must complete successfully."""
    raw_dir = tmp_path / "raw" / "sec"
    raw_dir.mkdir(parents=True)
    raw_8k = {**RAW, "source_id": "nvda-8k-2026-03-01", "form": "8-K",
              "filing_date": "2026-03-01", "sections": {"body": "Some 8-K text."}}
    raw_dir.joinpath("nvda-8k-2026-03-01.json").write_text(json.dumps(raw_8k))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps(
        {"nvda-8k-2026-03-01": {"accession": "0001-26-2", "processed": False}}))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe.anchor_claude, "extract_source", lambda raw, runner=None: [])

    def _must_not_be_called(raw):
        raise AssertionError("leg_xbrl.extract must not be called for 8-K")

    monkeypatch.setattr(pipe.leg_xbrl, "extract", _must_not_be_called)

    done = pipe.run(today="2026-06-07")
    assert done == ["nvda-8k-2026-03-01"]
    state = json.loads((tmp_path / "raw" / "_state.json").read_text())
    assert state["nvda-8k-2026-03-01"]["processed"] is True


def test_xbrl_value_error_does_not_kill_pipeline(tmp_path, monkeypatch):
    """If leg_xbrl.extract raises ValueError (e.g. no XBRL revenue), pipeline continues."""
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(pipe.leg_xbrl, "extract",
                        lambda raw: (_ for _ in ()).throw(ValueError("no XBRL revenue")))

    done = pipe.run(today="2026-06-07")
    assert done == ["nvda-10k-2026-02-26"]
    state = json.loads((tmp_path / "raw" / "_state.json").read_text())
    assert state["nvda-10k-2026-02-26"]["processed"] is True


def test_missing_raw_file_skipped(tmp_path, monkeypatch):
    """A source whose raw JSON file is absent is skipped; the other source succeeds."""
    raw_dir = tmp_path / "raw" / "sec"
    raw_dir.mkdir(parents=True)
    # Only write the second source's file; first is intentionally absent.
    sid_missing = "nvda-10k-2025-01-01"
    sid_good = "nvda-10k-2026-02-26"
    raw_dir.joinpath(f"{sid_good}.json").write_text(json.dumps(RAW))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps({
        sid_missing: {"accession": "0000-00-0", "processed": False},
        sid_good: {"accession": "0001-26-1", "processed": False},
    }))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe.anchor_claude, "extract_source", lambda raw, runner=None: TRIPLES)
    monkeypatch.setattr(pipe.leg_xbrl, "extract", lambda raw: ([], []))

    done = pipe.run(today="2026-06-07")
    assert done == [sid_good]

    state = json.loads((tmp_path / "raw" / "_state.json").read_text())
    assert state[sid_good]["processed"] is True
    assert state[sid_missing]["processed"] is False


def test_crashing_source_isolated(tmp_path, monkeypatch):
    """If anchor_claude.extract_source raises for one source, only that source is skipped."""
    raw_dir = tmp_path / "raw" / "sec"
    raw_dir.mkdir(parents=True)
    sid_bad = "nvda-10k-2025-01-01"
    sid_good = "nvda-10k-2026-02-26"
    raw_bad = {**RAW, "source_id": sid_bad, "filing_date": "2025-01-01"}
    raw_dir.joinpath(f"{sid_bad}.json").write_text(json.dumps(raw_bad))
    raw_dir.joinpath(f"{sid_good}.json").write_text(json.dumps(RAW))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps({
        sid_bad: {"accession": "0000-00-0", "processed": False},
        sid_good: {"accession": "0001-26-1", "processed": False},
    }))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe.leg_xbrl, "extract", lambda raw: ([], []))

    def _extract_source_side_effect(raw, runner=None):
        if raw["source_id"] == sid_bad:
            raise RuntimeError("simulated anchor crash")
        return TRIPLES

    monkeypatch.setattr(pipe.anchor_claude, "extract_source", _extract_source_side_effect)

    done = pipe.run(today="2026-06-07")
    assert done == [sid_good]

    state = json.loads((tmp_path / "raw" / "_state.json").read_text())
    assert state[sid_good]["processed"] is True
    assert state[sid_bad]["processed"] is False


def test_domain_violating_edge_dropped(tmp_path, monkeypatch):
    """Anchor returns one valid triple + one domain-violating triple.
    Only the valid one must reach content/, and lint must pass.
    """
    raw_dir = tmp_path / "raw" / "sec"
    raw_dir.mkdir(parents=True)
    raw_dir.joinpath("nvda-10k-2026-02-26.json").write_text(json.dumps(RAW))
    (tmp_path / "raw" / "_state.json").write_text(json.dumps(
        {"nvda-10k-2026-02-26": {"accession": "0001-26-1", "processed": False}}))
    monkeypatch.setattr(pipe, "RAW", tmp_path / "raw")
    monkeypatch.setattr(pipe, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(pipe.leg_xbrl, "extract", lambda raw: ([], []))

    # One valid edge (Company COMPETES_WITH Company) + one domain violation
    # (Technology IN_SEGMENT Segment — Technology not in IN_SEGMENT domain)
    mixed_triples = [
        {"subject": "NVIDIA", "subject_type": "Company", "predicate": "COMPETES_WITH",
         "object": "Advanced Micro Devices", "object_type": "Company",
         "evidence": "NVIDIA competes with AMD.", "as_of": "2026-Q1",
         "source": "nvda-10k-2026-02-26", "extractor": "claude"},
        {"subject": "NVLink", "subject_type": "Technology", "predicate": "IN_SEGMENT",
         "object": "Data Center", "object_type": "Segment",
         "evidence": "NVLink belongs to the Data Center segment.",
         "as_of": "2026-Q1", "source": "nvda-10k-2026-02-26", "extractor": "claude"},
    ]
    monkeypatch.setattr(pipe.anchor_claude, "extract_source", lambda raw, runner=None: mixed_triples)

    done = pipe.run(today="2026-06-07")
    assert done == ["nvda-10k-2026-02-26"]

    import frontmatter
    nv = frontmatter.load(tmp_path / "content" / "entities" / "nvidia.md")
    pred_targets = [(r["predicate"], r["target"]) for r in nv["relations"]]
    assert ("COMPETES_WITH", "amd") in pred_targets       # valid edge kept

    # Domain-violating edge must NOT appear in any entity page
    nvlink_path = tmp_path / "content" / "entities" / "nvlink.md"
    if nvlink_path.exists():
        nvlink_page = frontmatter.load(nvlink_path)
        for r in nvlink_page.get("relations") or []:
            assert not (r["predicate"] == "IN_SEGMENT"), \
                "Domain-violating IN_SEGMENT edge must not be written to content/"

    # Lint must pass
    errors = lint_dir(tmp_path / "content")
    assert errors == [], f"Lint errors: {errors}"
