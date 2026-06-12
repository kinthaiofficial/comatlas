"""Clip a verbatim evidence sentence to a <=15-word excerpt centered on the focus phrase,
with ellipsis where trimmed. Honors red line #5 (short quotes only). Pure, deterministic."""

ELLIPSIS = "…"


def short_quote(evidence: str, focus: str = "", max_words: int = 15) -> str:
    evidence = (evidence or "").strip()
    if not evidence:
        return ""
    words = evidence.split()
    if len(words) <= max_words:
        return evidence
    # Locate the focus phrase's first word among tokens (case-insensitive, punctuation-trimmed)
    idx = 0
    if focus:
        key = focus.split()[0].strip(",.;:\"'()").lower()
        for i, w in enumerate(words):
            if w.strip(",.;:\"'()").lower() == key:
                idx = i
                break
    # Window of max_words centered on idx
    half = max_words // 2
    start = max(0, idx - half)
    end = min(len(words), start + max_words)
    start = max(0, end - max_words)
    excerpt = " ".join(words[start:end])
    if start > 0:
        excerpt = ELLIPSIS + " " + excerpt
    if end < len(words):
        excerpt = excerpt + " " + ELLIPSIS
    return excerpt
