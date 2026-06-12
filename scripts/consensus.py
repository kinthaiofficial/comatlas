"""Edge scoring. M1: single-anchor scoring. M2 adds cross-vendor voting (merge_votes + score)."""


def score_m1(edge: dict) -> str:
    if edge.get("from_structured"):
        return "high"            # XBRL / Wikidata: trusted, no voting
    return "medium"              # single LLM vote, grounding deferred to M2


def merge_votes(edges: list[dict]) -> dict:
    """Group normalized edges by (subject, predicate, target). Each record unions the voting
    extractors and corroborating sources, and keeps per-source evidence for grounding.

    Provenance honesty (red line #8): extractor strings are unioned verbatim — `human` counts
    as a vote and is never relabeled to an LLM extractor (or vice versa)."""
    by: dict = {}
    for e in edges:
        key = (e["subject"], e["predicate"], e["target"])
        rec = by.get(key)
        if rec is None:
            rec = {"key": key, "edge": dict(e), "extractors": set(), "sources": set(),
                   "evidence": [], "from_structured": False}
            by[key] = rec
        rec["extractors"].update(e.get("extractors", []))
        rec["sources"].add(e["source"])
        rec["from_structured"] = rec["from_structured"] or bool(e.get("from_structured"))
        if e.get("evidence"):
            rec["evidence"].append({"source": e["source"], "text": e["evidence"]})
    return by


def score(rec: dict, grounding_ok: bool) -> str:
    """M2 confidence (solution §5.2): structured → high; grounding failure → low; otherwise
    agreement (distinct extractors) + corroboration (distinct sources). Weak-model silence
    just means fewer extractors — it never demotes (FR-8)."""
    if rec["from_structured"]:
        return "high"                               # XBRL / Wikidata: trusted, no voting/grounding
    if not grounding_ok:
        return "low"                                # evidence absent or doesn't support the edge
    agree = len(set(rec["extractors"]))
    corro = len(set(rec["sources"]))
    if agree >= 2 and corro >= 2:
        return "high"
    if agree >= 1:
        return "medium"
    return "low"
