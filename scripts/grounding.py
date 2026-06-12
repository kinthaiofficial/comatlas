"""Grounding (FR-9): does the quoted evidence exist in the source AND support the edge?

(a) presence  — deterministic rapidfuzz partial match (catches LLM paraphrase/fabrication);
(b) entailment — MiniMax M3 verdict (decision M1: independent paid quota, no claude -p
    contention; M3 is a reasoning model so we parse the last {...} JSON, ignoring <think> prose).

Either check failing -> the caller scores the edge `low` (red line #3 keeps it unpublished)."""
import json, os
from rapidfuzz import fuzz

MODEL = os.environ.get("COMATLAS_GROUNDING_MODEL", "MiniMax-M3")
BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
FUZZ_THRESHOLD = 88


def evidence_in_source(evidence: str, source_text: str) -> bool:
    return fuzz.partial_ratio(" ".join((evidence or "").lower().split()),
                              " ".join((source_text or "").lower().split())) >= FUZZ_THRESHOLD


def _client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["MINIMAX_API_KEY"], base_url=BASE_URL)


def entailed(evidence: str, edge: dict, client=None) -> bool:
    client = client or _client()
    claim = f"{edge['subject']} {edge['predicate']} {edge['target']}"
    prompt = ("You are a strict fact checker. Judge ONLY from the sentence; if it does not clearly "
              f"state the claim, supported is false.\nSentence: {evidence}\nClaim: {claim}\n"
              'Respond with ONLY JSON: {"supported": true|false, "reason": "..."}')
    resp = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content or ""
    s, e = text.rfind("{"), text.rfind("}")            # last JSON object; ignore <think> prose
    return bool(json.loads(text[s:e + 1])["supported"])


def grounding_ok(evidence: str, source_text: str, edge: dict, client=None) -> bool:
    if not evidence_in_source(evidence, source_text):
        return False
    return entailed(evidence, edge, client=client)
