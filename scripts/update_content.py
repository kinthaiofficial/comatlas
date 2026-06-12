"""Merge scored edges + facts into content/ markdown (frontmatter is the single source of truth).

YAML date round-trip: python-frontmatter uses yaml.safe_dump which auto-quotes strings that
look like ISO dates (e.g. '2026-06-07' → YAML single-quoted string). On load, single-quoted
YAML strings are returned as Python str, so last_updated round-trips correctly as a string.
"""
from pathlib import Path
import frontmatter
from scripts.quote import short_quote

AUTO_BEGIN = "<!-- AUTO-RELATIONS:BEGIN -->"
AUTO_END = "<!-- AUTO-RELATIONS:END -->"
SUMMARY_BEGIN = "<!-- SUMMARY:BEGIN -->"
SUMMARY_END = "<!-- SUMMARY:END -->"
RANK = {"low": 0, "medium": 1, "high": 2}


def _dump(post: frontmatter.Post, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post) + "\n")


def _stub(content: Path, eid: str, etype: str, label: str, today: str) -> frontmatter.Post:
    """Load existing page or create a minimal stub that satisfies the linter."""
    p = content / "entities" / f"{eid}.md"
    if p.exists():
        return frontmatter.load(str(p))
    post = frontmatter.Post(f"{AUTO_BEGIN}\n{AUTO_END}\n")
    post.metadata = {
        "type": etype,
        "id": eid,
        "label": label,
        "aliases": [label],
        "confidence": "medium",
        "publish": True,
        "last_updated": today,
        "sources": [],
        "relations": [],
    }
    return post


def _ensure_source_page(content: Path, meta: dict) -> None:
    p = content / "sources" / f"{meta['id']}.md"
    if not p.exists():
        post = frontmatter.Post("")
        post.metadata = {k: meta[k] for k in ("id", "kind", "title", "url", "date")}
        _dump(post, p)


def _merge_edge(meta: dict, e: dict) -> None:
    """Upsert edge into meta['relations'] using (predicate, target) as dedup key."""
    for r in meta.setdefault("relations", []):
        if r["predicate"] == e["predicate"] and r["target"] == e["target"]:
            # Update as_of to the later quarter/date
            if e["as_of"] > r["as_of"]:
                r["as_of"] = e["as_of"]
            # Append new source to corroborates (primary source unchanged)
            if e["source"] != r["source"]:
                corroborates = r.setdefault("corroborates", [])
                if e["source"] not in corroborates:
                    corroborates.append(e["source"])
            # Union extractors (sorted for stability)
            r["extractors"] = sorted(set(r["extractors"]) | set(e["extractors"]))
            # Raise confidence only if new edge is higher
            if RANK[e["confidence"]] > RANK[r["confidence"]]:
                r["confidence"] = e["confidence"]
            # Backfill the evidence short-quote if missing and this edge supplies evidence
            if not r.get("quote") and e.get("evidence"):
                r["quote"] = short_quote(e["evidence"], e.get("target_label", ""))
            return
    # New edge
    meta["relations"].append({
        "predicate": e["predicate"],
        "target": e["target"],
        "as_of": e["as_of"],
        "source": e["source"],
        "confidence": e["confidence"],
        "extractors": list(e["extractors"]),
        "corroborates": [],
        "quote": short_quote(e.get("evidence", ""), e.get("target_label", "")),
    })


def _render_auto_block(meta: dict) -> str:
    """Render the markdown table for relations and facts (low-confidence edges excluded)."""
    rows = [
        "| relation | target | as of | confidence | basis | source |",
        "|---|---|---|---|---|---|",
    ]
    for r in meta.get("relations") or []:
        if r["confidence"] == "low":
            continue  # Red line #3: low-confidence edges never rendered
        basis = (r.get("quote") or "").replace("|", "\\|")
        rows.append(
            f"| {r['predicate']} | [[{r['target']}]] | {r['as_of']}"
            f" | {r['confidence']} | {basis} | [[sources/{r['source']}|{r['source']}]] |"
        )

    facts = meta.get("facts") or []
    if facts:
        rows += [
            "",
            "| metric | value | period | source |",
            "|---|---|---|---|",
        ]
        for f in facts:
            rows.append(
                f"| {f['metric']} | {f['value']:,} {f.get('unit', '')} | {f['period']}"
                f" | [[sources/{f['source']}|{f['source']}]] |"
            )
    return "\n".join(rows)


def _rewrite_body(post: frontmatter.Post, page_id: str = "") -> str:
    """Replace the AUTO block in the body while preserving hand-written prose."""
    body = post.content
    if AUTO_BEGIN not in body:
        body += f"\n{AUTO_BEGIN}\n{AUTO_END}\n"
    # Guard: END must not appear before BEGIN, and END must exist after BEGIN
    begin_idx = body.index(AUTO_BEGIN)
    end_idx = body.find(AUTO_END)
    if end_idx == -1 or end_idx < begin_idx:
        raise ValueError(
            f"Malformed AUTO block in page '{page_id}': "
            f"{AUTO_END} must appear after {AUTO_BEGIN}"
        )
    head, rest = body.split(AUTO_BEGIN, 1)
    _, tail = rest.split(AUTO_END, 1)
    return f"{head}{AUTO_BEGIN}\n{_render_auto_block(post.metadata)}\n{AUTO_END}{tail}"


def _rewrite_summary(post: frontmatter.Post, text: str) -> str:
    """Upsert the managed SUMMARY block at the top of the body, preserving everything else."""
    block = f"{SUMMARY_BEGIN}\n{text.strip()}\n{SUMMARY_END}"
    body = post.content
    if SUMMARY_BEGIN in body and SUMMARY_END in body:
        head, rest = body.split(SUMMARY_BEGIN, 1)
        _, tail = rest.split(SUMMARY_END, 1)
        return f"{head}{block}{tail}"
    return f"{block}\n\n{body}"


def apply(content: Path, *, edges: list, facts: list, source_meta: dict, today: str,
          summaries: dict | None = None) -> None:
    """Merge edges and facts into entity pages; create stub pages and source pages as needed.

    Args:
        content:     Root content directory (entities/ and sources/ subdirs live here).
        edges:       List of scored edge dicts from the extraction pipeline.
        facts:       List of fact dicts (metric/value/unit/period/source/confidence/extractors).
        source_meta: Metadata dict for the source document (id/kind/title/url/date).
        today:       ISO date string "YYYY-MM-DD" for last_updated.
    """
    content = Path(content)
    summaries = summaries or {}
    _ensure_source_page(content, source_meta)

    # Accumulate all pages to write (subject + target from edges, entity from facts)
    touched: dict[str, frontmatter.Post] = {}

    for e in edges:
        for eid, etype, label in (
            (e["subject"], e["subject_type"], e.get("subject_label", e["subject"])),
            (e["target"],  e["target_type"],  e.get("target_label",  e["target"])),
        ):
            if eid not in touched:
                touched[eid] = _stub(content, eid, etype, label, today)
        _merge_edge(touched[e["subject"]].metadata, e)

    for fact in facts:
        fact = dict(fact)
        eid = fact.pop("entity", "nvidia")
        if eid not in touched:
            touched[eid] = _stub(content, eid, "Company", eid, today)
        flist = touched[eid].metadata.setdefault("facts", [])
        # Replace any existing fact with same (metric, period)
        flist[:] = [
            x for x in flist
            if not (x["metric"] == fact["metric"] and x["period"] == fact["period"])
        ]
        flist.append({
            **{k: fact[k] for k in ("metric", "value", "period", "source", "confidence", "extractors")},
            "unit": fact.get("unit", ""),
        })

    # Entities that only get a summary this run (no edges/facts) still need writing
    for eid in summaries:
        if eid not in touched:
            touched[eid] = _stub(content, eid, "Company", eid, today)

    for eid, post in touched.items():
        m = post.metadata
        m["last_updated"] = today
        if source_meta["id"] not in m.setdefault("sources", []):
            m["sources"].append(source_meta["id"])
        # Publish gate: low-confidence pages must not be published (red line #3)
        m["publish"] = m.get("confidence") != "low"
        post.content = _rewrite_body(post, page_id=eid)
        if eid in summaries:
            m["summary_by"] = "claude"
            post.content = _rewrite_summary(post, summaries[eid])
        _dump(post, content / "entities" / f"{eid}.md")
