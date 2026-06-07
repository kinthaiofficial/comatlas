"""Edge scoring. M1: single-anchor scoring. M2 adds cross-vendor voting (see merge_votes)."""


def score_m1(edge: dict) -> str:
    if edge.get("from_structured"):
        return "high"            # XBRL / Wikidata: trusted, no voting
    return "medium"              # single LLM vote, grounding deferred to M2
