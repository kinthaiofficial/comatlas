import json
from types import SimpleNamespace
from scripts.extract import second_minimax as mm

RESP = {"triples": [{"subject": "NVIDIA", "subject_type": "Company", "predicate": "MANUFACTURED_BY",
        "object": "TSMC", "object_type": "Fab",
        "evidence": "NVIDIA relies on TSMC to manufacture its GPUs.", "as_of": "2026-Q1"}]}


class FakeOpenAI:
    """OpenAI-compatible stub returning a forced record_triples tool call."""
    def __init__(self, resp=RESP):
        self.chat = self; self.completions = self; self.kwargs = None; self.resp = resp

    def create(self, **kw):
        self.kwargs = kw
        msg = SimpleNamespace(tool_calls=[SimpleNamespace(
            function=SimpleNamespace(name="record_triples", arguments=json.dumps(self.resp)))])
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_extract_source_tags_minimax_provenance():
    raw = {"source_id": "s1", "as_of": "2026-Q1",
           "sections": {"Item 1": "NVIDIA relies on TSMC to manufacture its GPUs."}}
    c = FakeOpenAI()
    triples = mm.extract_source(raw, client=c)
    assert triples[0]["extractor"] == "minimax" and triples[0]["source"] == "s1"
    assert triples[0]["predicate"] == "MANUFACTURED_BY"
    assert c.kwargs["tools"][0]["function"]["name"] == "record_triples"   # shared schema prompt (FR-5)


def test_same_closed_set_schema_as_anchor():
    from scripts.extract.anchor_claude import triples_schema
    assert mm.openai_tool()["function"]["parameters"] == triples_schema()   # one schema, two vendors


def test_invalid_vote_triple_dropped_not_raised():
    bad = {"triples": [
        {"subject": "X", "subject_type": "Startup", "predicate": "ACQUIRED", "object": "Y",
         "object_type": "Company", "evidence": "e", "as_of": "2026-Q1"},                 # out of closed set
        {"subject": "NVIDIA", "subject_type": "Company", "predicate": "MANUFACTURED_BY", "object": "TSMC",
         "object_type": "Fab", "evidence": "NVIDIA relies on TSMC.", "as_of": "2026-Q1"}]}
    raw = {"source_id": "s1", "as_of": "2026-Q1", "sections": {"x": "NVIDIA relies on TSMC."}}
    triples = mm.extract_source(raw, client=FakeOpenAI(bad))
    assert len(triples) == 1 and triples[0]["predicate"] == "MANUFACTURED_BY"   # invalid dropped, valid kept


def test_per_chunk_failure_is_tolerated():
    """A 422/rate-limit on one chunk must not abort the whole second vote (real-run lesson:
    MiniMax content-moderation 422s on sensitive geopolitics text)."""
    big = "NVIDIA relies on TSMC. " * 700                    # > 12000 chars -> 2 chunks
    raw = {"source_id": "s1", "as_of": "2026-Q1", "sections": {"x": big}}

    class Flaky:
        def __init__(self): self.chat = self; self.completions = self; self.n = 0
        def create(self, **kw):
            self.n += 1
            if self.n == 1:
                raise RuntimeError("Error code: 422 - input new_sensitive")
            return FakeOpenAI().create(**kw)

    triples = mm.extract_source(raw, client=Flaky())
    assert len(triples) >= 1                                  # chunk-2 votes survive the chunk-1 failure


# ── live smoke (real MiniMax key; excluded by default via -m 'not live') ──────
import pytest

@pytest.mark.live
def test_live_minimax_returns_toolcall_triples():
    raw = {"source_id": "nvda-10k-2026-02-25", "as_of": "2026-Q1",
           "sections": {"x": "We utilize foundries, such as Taiwan Semiconductor Manufacturing "
                             "Company Limited, or TSMC, to produce our semiconductor wafers."}}
    triples = mm.extract_source(raw)            # real client from MINIMAX_API_KEY
    assert all(t["extractor"] == "minimax" for t in triples)
    assert any(t["object"].upper().startswith("TSMC") or "TSMC" in t["object"].upper() for t in triples)
