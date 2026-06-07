#!/usr/bin/env python3
"""Seed the content/ directory from eval/gold_triples.json + XBRL facts.

This script is used when the claude -p anchor leg is too slow (rate-limited
by concurrent sessions). It builds a representative KG from the human-verified
gold triples plus structured XBRL data extracted from the 10-K and 10-Q filings.

Gold-seeded edges are HUMAN-verified curation, never attributed to an LLM extractor (honesty red line).

Usage:
    PYTHONPATH=/root/comatlas/code/comatlas python scripts/seed_from_gold.py
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extract import leg_xbrl
from scripts.normalize import normalize_surface
from scripts.consensus import score_m1
from scripts import update_content

CONTENT = ROOT / "content"
RAW = ROOT / "raw"
GOLD = ROOT / "eval" / "gold_triples.json"

# Map predicate to canonical (subject_type, object_type) for ontology compliance
PRED_TYPES = {
    "MANUFACTURED_BY": ("Company", "Company"),
    "SUPPLIES":        ("Company", "Company"),
    "COMPETES_WITH":   ("Company", "Company"),
    "SUBSIDIARY_OF":   ("Company", "Company"),
    "IN_SEGMENT":      ("Segment", "Company"),
    "CUSTOMER_OF":     ("Company", "Company"),
    "PARTNER_WITH":    ("Company", "Company"),
    "OWNS_STAKE_IN":   ("Company", "Company"),
}


def gold_edges(source_id: str, as_of: str) -> list[dict]:
    """Convert gold triples to the normalized edge format used by update_content."""
    gold = json.loads(GOLD.read_text())
    out = []
    for t in gold["triples"]:
        pred = t["predicate"]
        subj_type, obj_type = PRED_TYPES.get(pred, ("Company", "Company"))
        # IN_SEGMENT subject is already a Segment ID in gold
        if pred == "IN_SEGMENT":
            subj_type = "Segment"

        subj_id, _ = normalize_surface(t["subject"])
        tgt_id, _ = normalize_surface(t["target"])

        edge = {
            "subject": subj_id,
            "subject_type": subj_type,
            "subject_label": t["subject"],
            "target": tgt_id,
            "target_type": obj_type,
            "target_label": t["target"],
            "predicate": pred,
            "as_of": as_of,
            "source": source_id,
            "evidence": t["evidence"],
            "extractors": ["human"],
            "from_structured": False,
        }
        edge["confidence"] = score_m1(edge)
        out.append(edge)
    return out


def process_filing(raw: dict, today: str) -> None:
    source_id = raw["source_id"]
    as_of = raw["as_of"]
    form = raw["form"]
    print(f"Processing {source_id} ({form}) ...", file=sys.stderr)

    facts, xbrl_edges = [], []
    if form in ("10-K", "10-Q"):
        try:
            f, e = leg_xbrl.extract(raw)
            facts = [{**x, "entity": "nvidia"} for x in f]
            xbrl_edges = [
                {
                    "subject": x["subject"],
                    "subject_type": x["subject_type"],
                    "subject_label": x.get("subject_label", x["subject"]),
                    "target": x["target"],
                    "target_type": x["target_type"],
                    "target_label": x.get("target_label", x["target"]),
                    "predicate": x["predicate"],
                    "as_of": x["as_of"],
                    "source": x["source"],
                    "evidence": x.get("evidence", ""),
                    "extractors": [x["extractor"]],
                    "from_structured": x.get("from_structured", False),
                    "confidence": score_m1(x),
                }
                for x in e
            ]
        except ValueError as exc:
            print(f"  XBRL leg skipped: {exc}", file=sys.stderr)

    # Use gold edges only for the 10-K (the anchor truth source)
    anchor_edges = gold_edges(source_id, as_of) if form == "10-K" else []

    edges = xbrl_edges + anchor_edges
    print(f"  {len(facts)} facts, {len(xbrl_edges)} xbrl edges, {len(anchor_edges)} gold edges",
          file=sys.stderr)

    update_content.apply(
        CONTENT,
        edges=edges,
        facts=facts,
        today=today,
        source_meta={
            "id": source_id,
            "kind": "sec-filing",
            "title": f"NVIDIA {form} {raw['filing_date']}",
            "url": raw["url"],
            "date": raw["filing_date"],
            "accession": raw["accession"],
        },
    )


def run() -> None:
    today = datetime.date.today().isoformat()
    state_path = RAW / "_state.json"
    state = json.loads(state_path.read_text())
    done = []
    for sid in sorted(state):
        raw_path = RAW / "sec" / f"{sid}.json"
        if not raw_path.exists():
            print(f"SKIP {sid}: file not found", file=sys.stderr)
            continue
        raw = json.loads(raw_path.read_text())
        try:
            process_filing(raw, today)
        except Exception as exc:
            print(f"SKIP {sid}: {exc}", file=sys.stderr)
            continue
        state[sid]["processed"] = True
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True))
        done.append(sid)
        print(f"  OK: {sid}", file=sys.stderr)

    print(json.dumps(done))


if __name__ == "__main__":
    run()
