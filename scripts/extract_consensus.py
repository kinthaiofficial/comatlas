#!/usr/bin/env python3
"""Pipeline entry: process every unprocessed raw source -> normalized scored edges -> content/."""
import datetime
import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path when invoked directly (e.g. python scripts/extract_consensus.py)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.extract import anchor_claude, leg_xbrl, second_minimax
from scripts.normalize import normalize_surface
from scripts.ontology import load_predicates, edge_satisfies_ontology
from scripts import update_content, consensus, grounding, review_queue

ROOT = Path(__file__).resolve().parents[1]
RAW, CONTENT = ROOT / "raw", ROOT / "content"


def normalize_triple(t: dict) -> dict:
    """Anchor triple (subject/object surfaces) -> canonical edge dict."""
    sid, _ = normalize_surface(t["subject"])
    tid, _ = normalize_surface(t["object"])
    return {"subject": sid, "subject_type": t["subject_type"], "subject_label": t["subject"],
            "target": tid, "target_type": t["object_type"], "target_label": t["object"],
            "predicate": t["predicate"], "as_of": t["as_of"], "source": t["source"],
            "evidence": t["evidence"], "extractors": [t["extractor"]],
            "from_structured": t.get("from_structured", False)}


def normalize_xbrl_edge(e: dict) -> dict:
    """XBRL edges already use canonical ids; reshape to the same edge dict."""
    return {"subject": e["subject"], "subject_type": e["subject_type"],
            "subject_label": e.get("subject_label", e["subject"]),
            "target": e["target"], "target_type": e["target_type"],
            "target_label": e.get("target_label", e["target"]),
            "predicate": e["predicate"], "as_of": e["as_of"], "source": e["source"],
            "evidence": e.get("evidence", ""), "extractors": [e["extractor"]],
            "from_structured": e.get("from_structured", False)}


def _all_text(raw: dict) -> str:
    return "\n".join(raw.get("sections", {}).values())


def _minimax_client():
    """A reusable MiniMax client for grounding, or None when no key is configured (tests stub
    grounding.grounding_ok so the client is never used there)."""
    if not os.environ.get("MINIMAX_API_KEY"):
        return None
    from openai import OpenAI
    return OpenAI(api_key=os.environ["MINIMAX_API_KEY"],
                  base_url=os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"))


def process_source(raw: dict, today: str) -> None:
    """M2a: anchor (Claude) + second vote (MiniMax) → ontology guard → merge_votes →
    grounding (narrative only) → score → low/conflict to review queue → content."""
    facts, structured = [], []
    if raw["form"] in ("10-K", "10-Q"):
        try:
            f, e = leg_xbrl.extract(raw)
            facts += [{**x, "entity": "nvidia"} for x in f]
            structured += [normalize_xbrl_edge(x) for x in e]
        except ValueError as exc:
            print(f"[extract_consensus] XBRL leg skipped for {raw['source_id']}: {exc}",
                  file=sys.stderr)

    narrative = [normalize_triple(t)
                 for t in anchor_claude.extract_source(raw, checkpoint_dir=RAW / "_partial")]
    narrative += [normalize_triple(t) for t in second_minimax.extract_source(raw)]

    # Ontology domain/range guard BEFORE voting (drop violations; never enter content/queue)
    predicates = load_predicates()
    valid = []
    for e in narrative + structured:
        ok, reason = edge_satisfies_ontology(e, predicates)
        if ok:
            valid.append(e)
        else:
            print(f"DROP {e['subject']} {e['predicate']} {e['target']}: {reason}", file=sys.stderr)

    by = consensus.merge_votes(valid)
    client = _minimax_client()
    text = _all_text(raw)
    edges, queue_items = [], []
    for rec in by.values():
        e = dict(rec["edge"])
        e["extractors"] = sorted(set(rec["extractors"]))      # union; human never relabeled (#8)
        if rec["from_structured"]:
            e["confidence"] = "high"                           # XBRL: trusted, no grounding
        else:
            ev = rec["evidence"][0]["text"] if rec["evidence"] else ""
            g_ok = grounding.grounding_ok(ev, text, e, client=client)
            e["confidence"] = consensus.score(rec, g_ok)
            if e["confidence"] == "low":
                queue_items.append({"kind": "low", "subject": e["subject"], "predicate": e["predicate"],
                                    "candidates": [{"target": e["target"], "extractors": e["extractors"],
                                                    "sources": sorted(rec["sources"]),
                                                    "evidence": rec["evidence"]}]})
        edges.append(e)

    update_content.apply(CONTENT, edges=edges, facts=facts, today=today,
                         source_meta={"id": raw["source_id"], "kind": "sec-filing",
                                      "title": f"NVIDIA {raw['form']} {raw['filing_date']}",
                                      "url": raw["url"], "date": raw["filing_date"],
                                      "accession": raw["accession"]})
    review_queue.append_items(ROOT / "review_queue.md", queue_items, today=today)


def run(today: str | None = None) -> list[str]:
    """Process every unprocessed raw source and return list of successfully processed source ids.

    Each source is handled in isolation: a failure (missing file or extraction error) prints
    a SKIP message to stderr and leaves that source's processed flag as False, so the next
    run will retry it.  Successful sources are marked processed=True and the state file is
    persisted immediately after each one, so progress is never lost if a later source crashes.
    """
    today = today or datetime.date.today().isoformat()
    state_path = RAW / "_state.json"
    state = json.loads(state_path.read_text())
    done = []
    for sid, st in sorted(state.items()):
        if st.get("processed"):
            continue
        try:
            raw = json.loads((RAW / "sec" / f"{sid}.json").read_text())
            process_source(raw, today)
        except Exception as exc:
            print(f"SKIP {sid}: {exc}", file=sys.stderr)
            continue
        st["processed"] = True
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True))
        done.append(sid)
    return done


if __name__ == "__main__":
    print(json.dumps(run()))
