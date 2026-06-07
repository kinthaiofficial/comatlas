"""Tests for M1 pipeline entry: extract_consensus.py + consensus.py."""
import json
import pytest
from scripts import extract_consensus as pipe

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
