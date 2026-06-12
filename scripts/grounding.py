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


# Supply-chain-accurate relationship sentences ({s}=subject, {t}=target). The ontology's
# glirel_label ("is manufactured by") reads wrong at company level ("NVIDIA is manufactured by
# TSMC" is literally false), so grounding uses its own glosses that match each predicate's meaning.
GLOSS = {
    "SUPPLIES": "{s} supplies goods or services to {t}",
    "CUSTOMER_OF": "{s} is a customer of {t}",
    "COMPETES_WITH": "{s} competes with {t}",
    "MANUFACTURED_BY": "{t} manufactures products or chips for {s}",
    "OWNS_STAKE_IN": "{s} owns an equity stake in {t}",
    "SUBSIDIARY_OF": "{s} is a subsidiary of {t}",
    "PARTNER_WITH": "{s} has a partnership or agreement with {t}",
    "IN_SEGMENT": "{s} is a business segment of {t}",
}


def _relationship(edge: dict) -> str:
    s = edge.get("subject_label") or edge["subject"]
    t = edge.get("target_label") or edge["target"]
    tmpl = GLOSS.get(edge["predicate"], "{s} " + edge["predicate"].replace("_", " ").lower() + " {t}")
    return tmpl.format(s=s, t=t)


def _context(evidence: str, source_text: str, window: int = 400) -> str:
    """A window of the source around the evidence, so list-style fragments ('such as AMD') are
    judged with their framing ('Our current competitors include ... such as AMD')."""
    if not source_text:
        return evidence
    words = evidence.split()
    key = " ".join(words[:6]).lower()
    low = source_text.lower()
    idx = low.find(key)
    if idx == -1 and words:
        idx = low.find(words[0].lower())
    if idx == -1:
        return evidence
    return source_text[max(0, idx - window): idx + len(evidence) + window]


def entailed(evidence: str, edge: dict, client=None, context: str | None = None) -> bool:
    client = client or _client()
    rel = _relationship(edge)
    passage = context or evidence
    prompt = ("You verify supply-chain relationships extracted from corporate filings. Judge ONLY from "
              "the passage. The relationship holds if the passage states OR directly implies it — ignore "
              "exact wording and treat standard shorthand (using a foundry = 'manufactured by'; appearing "
              "in the filer's competitor list = 'competes with') as support. Mark false only if the "
              "passage does not support the relationship at all.\n"
              f"Passage: {passage}\nRelationship: {rel}\n"
              'Reply with ONLY JSON: {"supported": true|false, "reason": "..."}')
    resp = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content or ""
    s, e = text.rfind("{"), text.rfind("}")            # last JSON object; ignore <think> prose
    return bool(json.loads(text[s:e + 1])["supported"])


def grounding_ok(evidence: str, source_text: str, edge: dict, client=None) -> bool:
    if not evidence_in_source(evidence, source_text):
        return False
    return entailed(evidence, edge, client=client, context=_context(evidence, source_text))
