"""Review queue (FR-16): low-confidence / conflict edges land here for a human to decide.
The agent NEVER auto-deletes or auto-resolves these (red line #2/#8). Append is idempotent —
each item carries a stable id marker so re-runs don't duplicate it."""
from pathlib import Path

HEADER = ("# Review queue\n\n"
          "Low-confidence and conflicting edges for human review. The maintenance agent writes "
          "here but never decides — you do. Resolve by editing `content/` and removing the block.\n")


def _item_id(item: dict) -> str:
    targets = ",".join(sorted(c["target"] for c in item.get("candidates", [])))
    return f"{item['kind']}:{item['subject']}:{item['predicate']}:{targets}"


def _render(item: dict, today: str) -> str:
    lines = [f"<!-- RQ:{_item_id(item)} -->",
             f"### [{item['kind']}] {item['subject']} {item['predicate']} — added {today}"]
    for c in item.get("candidates", []):
        lines.append(f"- candidate target `{c['target']}` "
                     f"(extractors: {', '.join(c.get('extractors', []))}; "
                     f"sources: {', '.join(c.get('sources', []))})")
        for ev in c.get("evidence", []):
            lines.append(f"  - evidence ({ev['source']}): \"{ev['text']}\"")
    return "\n".join(lines) + "\n"


def append_items(path, items: list[dict], today: str) -> int:
    """Append items whose id is not already present. Returns the number appended."""
    path = Path(path)
    items = [it for it in (items or []) if it.get("candidates")]
    if not items:
        return 0
    existing = path.read_text() if path.exists() else ""
    body = existing or (HEADER + "\n")
    added = 0
    for it in items:
        if f"<!-- RQ:{_item_id(it)} -->" in body:
            continue
        body += "\n" + _render(it, today)
        added += 1
    if added:
        path.write_text(body)
    return added
