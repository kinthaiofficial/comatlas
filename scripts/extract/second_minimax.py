"""Second vote: MiniMax M3 via OpenAI-compatible API (subscription key, sk-cp-).

Same closed-set schema as the anchor (FR-5). Votes only — never defines the canonical form.
M3 is a reasoning model; we force a `record_triples` tool call and parse tool_calls only.
Out-of-set / malformed triples are DROPPED (a vote may be noisy; that is not fatal)."""
import json, os
from scripts.extract.anchor_claude import triples_schema, RULES, _chunks
from scripts.ontology import load_entity_types, load_predicates

MODEL = os.environ.get("COMATLAS_SECOND_MODEL", "MiniMax-M3")
BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")


def openai_tool() -> dict:
    return {"type": "function",
            "function": {"name": "record_triples",
                         "description": "Record every explicitly supported supply-chain relation.",
                         "parameters": triples_schema()}}


def _valid(t: dict, types: set, preds: set) -> bool:
    return (t.get("subject_type") in types and t.get("object_type") in types
            and t.get("predicate") in preds
            and all(isinstance(t.get(k), str) and t.get(k) for k in ("subject", "object", "evidence", "as_of")))


def extract_source(raw: dict, client=None) -> list[dict]:
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["MINIMAX_API_KEY"], base_url=BASE_URL)
    types, preds = set(load_entity_types()), set(load_predicates())
    out = []
    for section, text in raw["sections"].items():
        for chunk in _chunks(text or ""):
            if not chunk.strip():
                continue
            resp = client.chat.completions.create(
                model=MODEL, tools=[openai_tool()],
                tool_choice={"type": "function", "function": {"name": "record_triples"}},
                messages=[{"role": "system", "content": RULES},
                          {"role": "user", "content": f"as_of hint: {raw['as_of']}\n<text>\n{chunk}\n</text>"}])
            for call in (resp.choices[0].message.tool_calls or []):
                for t in json.loads(call.function.arguments).get("triples", []):
                    if _valid(t, types, preds):
                        out.append({**t, "source": raw["source_id"], "extractor": "minimax",
                                    "section": section})
    return out
