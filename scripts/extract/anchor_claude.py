"""Anchor leg: schema-constrained extraction with Claude.
G13: runs on the Claude Code SUBSCRIPTION via headless `claude -p` (no API key).
The anchor DEFINES the canonical form; output triples carry verbatim evidence for grounding."""
import json, os, subprocess
from scripts.ontology import load_entity_types, load_predicates

MODEL = os.environ.get("COMATLAS_ANCHOR_MODEL", "sonnet")
CHUNK_CHARS = 12_000

class ExtractionError(RuntimeError):
    pass

RULES = """You extract supply-chain knowledge-graph triples from SEC filings and similar texts.
Rules:
- Record ONLY relations explicitly stated in the text. Never infer or use outside knowledge.
- Copy the single supporting sentence VERBATIM into `evidence`.
- Use the given closed sets for types and predicates. If a relation does not fit, skip it.
- `as_of` is the calendar quarter the statement refers to; default to the provided hint.
- Return zero triples if nothing qualifies."""

JSON_ONLY = 'Respond with ONLY a JSON object {"triples": [...]} matching the schema — no prose, no markdown fences.'

def triples_schema() -> dict:
    types = sorted(load_entity_types())
    preds = sorted(load_predicates())
    return {"type": "object", "required": ["triples"], "properties": {
        "triples": {"type": "array", "items": {"type": "object",
            "required": ["subject", "subject_type", "predicate", "object", "object_type", "evidence", "as_of"],
            "properties": {
                "subject": {"type": "string"}, "subject_type": {"enum": types},
                "predicate": {"enum": preds},
                "object": {"type": "string"}, "object_type": {"enum": types},
                "evidence": {"type": "string"}, "as_of": {"type": "string"}}}}}}

def claude_runner(prompt: str, model: str = MODEL) -> str:
    """Headless Claude Code call (subscription auth; in Actions via CLAUDE_CODE_OAUTH_TOKEN)."""
    r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise ExtractionError(f"claude CLI failed: {r.stderr[:500]}")
    return json.loads(r.stdout)["result"]

def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    return t.strip()

def _chunks(text: str):
    for i in range(0, len(text), CHUNK_CHARS):
        yield text[i:i + CHUNK_CHARS]

def _validate(data: dict) -> list[dict]:
    types, preds = load_entity_types(), set(load_predicates())
    triples = data["triples"]
    for t in triples:
        if t["subject_type"] not in types or t["object_type"] not in types:
            raise ValueError(f"type outside closed set: {t}")
        if t["predicate"] not in preds:
            raise ValueError(f"predicate outside closed set: {t}")
        for k in ("subject", "object", "evidence", "as_of"):
            if not isinstance(t.get(k), str) or not t[k]:
                raise ValueError(f"bad field {k}: {t}")
    return triples

def extract_chunk(runner, chunk: str, as_of_hint: str) -> list[dict]:
    prompt = (f"{RULES}\n{JSON_ONLY}\n\nJSON schema:\n{json.dumps(triples_schema())}\n\n"
              f"as_of hint: {as_of_hint}\n<text>\n{chunk}\n</text>")
    out = runner(prompt)
    try:
        return _validate(json.loads(strip_fences(out)))
    except Exception as e1:                              # one retry, feeding the error back
        out2 = runner(prompt + f"\n\nYour previous output was invalid: {e1}. {JSON_ONLY}")
        try:
            return _validate(json.loads(strip_fences(out2)))
        except Exception as e2:
            raise ExtractionError(f"anchor output invalid after retry: {e2}")

def extract_source(raw: dict, runner=None) -> list[dict]:
    runner = runner or claude_runner
    out = []
    for section, text in raw["sections"].items():
        for chunk in _chunks(text or ""):
            if not chunk.strip():
                continue
            for t in extract_chunk(runner, chunk, raw["as_of"]):
                out.append({**t, "source": raw["source_id"], "extractor": "claude",
                            "section": section})
    return out
