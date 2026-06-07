#!/usr/bin/env python3
"""Enforce the frontmatter schema + red lines over content/. Exit 1 on violations.
Rules source: CLAUDE.md (maintainer rules) + impl plan §2."""
import re, sys
from pathlib import Path

# Ensure repo root is on sys.path when invoked directly (e.g. python scripts/lint_frontmatter.py)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import frontmatter
from scripts.ontology import load_entity_types, load_predicates, load_alias_map

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CONF = {"high", "medium", "low"}
REL_REQUIRED = {"predicate", "target", "as_of", "source", "confidence", "extractors"}
FACT_REQUIRED = {"metric", "value", "period", "source", "confidence", "extractors"}
SRC_REQUIRED = {"id", "kind", "title", "url", "date"}

def lint_dir(content: Path) -> list[str]:
    errors: list[str] = []
    types, preds = load_entity_types(), load_predicates()

    entities_dir = content / "entities"
    sources_dir = content / "sources"

    pages = {p.stem: frontmatter.load(p) for p in entities_dir.glob("*.md")} if entities_dir.is_dir() else {}
    sources = {p.stem: frontmatter.load(p) for p in sources_dir.glob("*.md")} if sources_dir.is_dir() else {}
    known_ids = set(pages) | set(load_alias_map().values())

    for sid, post in sources.items():
        missing = SRC_REQUIRED - set(post.metadata)
        if missing:
            errors.append(f"sources/{sid}: missing {sorted(missing)}")

    for pid, post in pages.items():
        m = post.metadata
        e = lambda msg: errors.append(f"{pid}: {msg}")
        if m.get("id") != pid: e("id must equal filename")
        if not ID_RE.match(pid): e("bad id format")
        if m.get("type") not in types: e(f"type '{m.get('type')}' not in closed set")
        if m.get("confidence") not in CONF: e("bad page confidence")
        if m.get("confidence") == "low" and m.get("publish") is True:
            e("RED LINE: low-confidence page must not be published")
        for i, r in enumerate(m.get("relations") or []):
            w = f"relations[{i}]"
            missing = REL_REQUIRED - set(r)
            if missing: e(f"{w}: missing {sorted(missing)}"); continue
            spec = preds.get(r["predicate"])
            if spec is None: e(f"{w}: predicate '{r['predicate']}' not in closed set"); continue
            if r["target"] not in known_ids: e(f"{w}: target '{r['target']}' unresolvable")
            if r["confidence"] not in CONF: e(f"{w}: bad confidence")
            if r["source"] not in sources: e(f"{w}: source '{r['source']}' has no source page")
            if m.get("type") not in spec["domain"]:
                e(f"{w}: subject type {m.get('type')} violates domain({r['predicate']})")
            tgt = pages.get(r["target"])
            if tgt and tgt.metadata.get("type") not in spec["range"]:
                e(f"{w}: target type {tgt.metadata.get('type')} violates range({r['predicate']})")
        for i, f in enumerate(m.get("facts") or []):
            missing = FACT_REQUIRED - set(f)
            if missing: errors.append(f"{pid}: facts[{i}]: missing {sorted(missing)}")
            elif f["source"] not in sources:
                errors.append(f"{pid}: facts[{i}]: source '{f['source']}' has no source page")
    return errors

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "content"
    errs = lint_dir(root)
    for x in errs: print(f"LINT: {x}", file=sys.stderr)
    sys.exit(1 if errs else 0)
