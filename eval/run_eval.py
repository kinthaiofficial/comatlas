#!/usr/bin/env python3
"""Acceptance metrics: AC-1 (high-edge precision vs gold), AC-2 (source coverage), AC-4 (alias accuracy)."""
import json, sys
from pathlib import Path
import frontmatter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.normalize import normalize_surface


def collect_edges(content=None):
    content = content or ROOT / "content"
    out = []
    for p in (content / "entities").glob("*.md"):
        m = frontmatter.load(p).metadata
        out += [{"subject": m["id"], **{k: r[k] for k in ("predicate", "target", "confidence")},
                 "has_source": bool(r.get("source"))} for r in m.get("relations") or []]
    return out


def ac1_precision_high(edges, gold) -> float:
    """Precision of high edges, SCOPED to (subject, predicate) pairs present in gold —
    gold covers a subgraph; unscoped high edges aren't judged."""
    gold_set = {(t["subject"], t["predicate"], t["target"]) for t in gold["triples"]}
    scope = {(s, p) for s, p, _ in gold_set}
    judged = [e for e in edges if e["confidence"] == "high" and (e["subject"], e["predicate"]) in scope]
    if not judged:
        return 1.0
    return sum((e["subject"], e["predicate"], e["target"]) in gold_set for e in judged) / len(judged)


def ac2_source_coverage(edges) -> float:
    return sum(e["has_source"] for e in edges) / len(edges) if edges else 1.0


def ac4_alias_accuracy(cases) -> float:
    return (sum(normalize_surface(c["surface"])[0] == c["id"] for c in cases) / len(cases)) if cases else 1.0


if __name__ == "__main__":
    edges = collect_edges()
    gold = json.loads((ROOT / "eval" / "gold_triples.json").read_text())
    alias = json.loads((ROOT / "eval" / "alias_gold.json").read_text())
    rows = [("AC-1 high precision", ac1_precision_high(edges, gold), 0.90),
            ("AC-2 source coverage", ac2_source_coverage(edges), 1.00),
            ("AC-4 alias accuracy", ac4_alias_accuracy(alias["cases"]), 0.95)]
    bad = False
    for name, v, thr in rows:
        ok = v >= thr
        bad |= not ok
        print(f"{'OK ' if ok else 'FAIL'} {name}: {v:.3f} (>= {thr})")
    sys.exit(1 if bad and "--gate" in sys.argv else 0)
