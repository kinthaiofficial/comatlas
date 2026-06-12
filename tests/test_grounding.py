import json
from types import SimpleNamespace
from scripts import grounding as g

TEXT = "NVIDIA relies on TSMC to manufacture and test its newest products."
EDGE = {"subject": "nvidia", "predicate": "MANUFACTURED_BY", "target": "tsmc"}


class FakeMM:
    """OpenAI-compatible stub returning a JSON verdict as message.content (M3 style)."""
    def __init__(self, supported):
        self.supported = supported; self.chat = self; self.completions = self

    def create(self, **kw):
        body = f'<think>weighing…</think> {json.dumps({"supported": self.supported, "reason": "r"})}'
        msg = SimpleNamespace(content=body, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_verbatim_presence_is_deterministic():
    assert g.evidence_in_source("NVIDIA relies on TSMC to manufacture", TEXT)
    assert not g.evidence_in_source("NVIDIA acquired TSMC in 2025", TEXT)


def test_minor_whitespace_tolerated():
    assert g.evidence_in_source("NVIDIA  relies on   TSMC", TEXT)


def test_entailment_uses_minimax_client_and_ignores_think_prose():
    assert g.entailed("NVIDIA relies on TSMC to manufacture", EDGE, client=FakeMM(True))
    assert not g.entailed("TSMC is in Taiwan", EDGE, client=FakeMM(False))


def test_grounding_ok_requires_presence_and_entailment():
    assert g.grounding_ok("NVIDIA relies on TSMC to manufacture", TEXT, EDGE, client=FakeMM(True))
    # presence fails (fabricated evidence) -> low even if the (mocked) judge says supported
    assert not g.grounding_ok("NVIDIA acquired TSMC in 2025", TEXT, EDGE, client=FakeMM(True))
    # presence ok but judge says not supported -> low
    assert not g.grounding_ok("NVIDIA relies on TSMC to manufacture", TEXT, EDGE, client=FakeMM(False))
