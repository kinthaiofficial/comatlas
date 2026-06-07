import json
from pathlib import Path
from scripts.extract import anchor_claude

FIX = (Path(__file__).parent / "fixtures" / "anchor_response.json").read_text()

def ok_runner(prompt, model="sonnet"):
    return FIX

def test_schema_is_closed_set():
    item = anchor_claude.triples_schema()["properties"]["triples"]["items"]["properties"]
    assert "SUPPLIES" in item["predicate"]["enum"] and "ACQUIRED" not in item["predicate"]["enum"]
    assert set(item["subject_type"]["enum"]) == {"Chip","Company","DataCenter","Fab","Person","Product","Segment","Technology"}
    assert set(item.keys()) >= {"subject","subject_type","predicate","object","object_type","evidence","as_of"}

def test_extract_source_tags_provenance():
    raw = {"source_id": "nvda-10k-2026-02-26", "as_of": "2026-Q1",
           "sections": {"Item 1": "NVIDIA relies on TSMC to manufacture its GPUs."}}
    triples = anchor_claude.extract_source(raw, runner=ok_runner)
    assert all(t["source"] == "nvda-10k-2026-02-26" and t["extractor"] == "claude" for t in triples)
    assert triples[0]["predicate"] == "MANUFACTURED_BY"

def test_markdown_fences_stripped():
    triples = anchor_claude.extract_source(
        {"source_id": "s", "as_of": "2026-Q1", "sections": {"x": "text"}},
        runner=lambda p, model="sonnet": f"```json\n{FIX}\n```")
    assert triples[0]["predicate"] == "MANUFACTURED_BY"

def test_invalid_output_retried_once_then_raises():
    calls = []
    def bad_runner(prompt, model="sonnet"):
        calls.append(prompt)
        return "I cannot produce JSON, sorry."
    raw = {"source_id": "s", "as_of": "2026-Q1", "sections": {"x": "text"}}
    import pytest
    with pytest.raises(anchor_claude.ExtractionError):
        anchor_claude.extract_source(raw, runner=bad_runner)
    assert len(calls) == 2                      # one retry with the error fed back

def test_filer_name_injected_into_prompt():
    captured = []
    def capturing_runner(prompt, model="sonnet"):
        captured.append(prompt)
        return FIX
    raw = {"source_id": "nvda-10k-2026-02-26", "as_of": "2026-Q1", "filer": "NVIDIA",
           "sections": {"Item 1": "We manufacture GPUs."}}
    anchor_claude.extract_source(raw, runner=capturing_runner)
    assert captured, "runner was never called"
    assert "filing by NVIDIA" in captured[0], f"filer line not found in prompt: {captured[0][:300]}"

def test_schema_violation_rejected():
    rogue = json.dumps({"triples": [{"subject": "X", "subject_type": "Startup",
        "predicate": "ACQUIRED", "object": "Y", "object_type": "Company",
        "evidence": "e", "as_of": "2026-Q1"}]})
    import pytest
    with pytest.raises(anchor_claude.ExtractionError):
        anchor_claude.extract_source(
            {"source_id": "s", "as_of": "2026-Q1", "sections": {"x": "t"}},
            runner=lambda p, model="sonnet": rogue)


# ── live smoke ──────────────────────────────────────────────────────────────
import pytest

@pytest.mark.live
def test_live_anchor_extracts_known_relation():
    """Runs the real claude CLI against a paragraph from NVDA 10-K that contains TSMC mention."""
    import json, time
    from pathlib import Path

    raw_path = Path(__file__).resolve().parents[1] / "raw" / "sec" / "nvda-10k-2026-02-25.json"
    doc = json.loads(raw_path.read_text())

    item1 = doc["sections"]["Item 1"]
    idx = item1.find("TSMC")
    assert idx != -1, "TSMC not found in Item 1"
    # ~2000-char window around the TSMC mention
    start = max(0, idx - 200)
    chunk = item1[start: start + 2000]

    raw = {
        "source_id": doc["source_id"],
        "as_of": doc["as_of"],
        "sections": {"Item 1 (excerpt)": chunk},
    }

    t0 = time.time()
    triples = anchor_claude.extract_source(raw, runner=anchor_claude.claude_runner)
    elapsed = time.time() - t0

    print(f"\n[live smoke] elapsed={elapsed:.1f}s  triples={len(triples)}")
    for t in triples:
        print(f"  {t['subject_type']}:{t['subject']} --{t['predicate']}--> {t['object_type']}:{t['object']}")

    assert len(triples) >= 1, "Expected at least one triple from a paragraph with TSMC manufacturing mention"

    # evidence sentences must appear (first 40 chars) in the chunk text
    for t in triples:
        snippet = t["evidence"][:40]
        assert snippet in chunk, f"Evidence snippet not found in chunk: {snippet!r}"
