"""Deterministic leg: XBRL financial facts (trusted, no voting — FR-6).

Pure logic (to_facts_edges) is tested without network access.
Live extraction (extract) uses edgartools to pull XBRL from SEC EDGAR.

Period label heuristic
-----------------------
- 10-K: FY{year}  where year = the calendar year of the filing's period-of-report.
  NVIDIA's FY2026 ends 2026-01-25, so year = 2026 → "FY2026".
- 10-Q: Q{q}FY{year}  where q is derived from the filing's fiscal_period field
  (Q1/Q2/Q3) and year from fiscal_year.  Falls back to calendar quarter of
  period-of-report if fiscal metadata is unavailable.
"""
from scripts.normalize import normalize_surface, slugify

# XBRL label role used to resolve terse human-readable names for dimension members
_TERSE = "http://www.xbrl.org/2003/role/terseLabel"
_LABEL = "http://www.xbrl.org/2003/role/label"

# The XBRL axis that identifies reportable business segments
_SEGMENT_AXIS = "us-gaap:StatementBusinessSegmentsAxis"


# ---------------------------------------------------------------------------
# Pure / unit-testable layer
# ---------------------------------------------------------------------------

def to_facts_edges(
    fin: dict,
    *,
    entity: str,
    period: str,
    source: str,
    as_of: str,
) -> tuple[list, list]:
    """Convert a normalised financial dict to (facts, edges).

    fin must contain:
      - "revenue": int/float — total revenue in USD
      - "segments": dict[str, int/float] — segment name → revenue (optional)

    Returns:
      facts: list of fact dicts (metric, value, unit, period, source, confidence, extractors)
      edges: list of edge dicts matching the downstream edge shape
    """
    facts = [
        {
            "metric": "revenue",
            "value": fin["revenue"],
            "unit": "USD",
            "period": period,
            "source": source,
            "confidence": "high",
            "extractors": ["xbrl"],
        }
    ]
    edges: list = []

    for name, value in (fin.get("segments") or {}).items():
        sid, known = normalize_surface(name)
        if not known:
            sid = f"{entity}-{slugify(name)}"  # G10: company-prefixed segment ids

        facts.append(
            {
                "metric": f"segment_revenue:{sid}",
                "value": value,
                "unit": "USD",
                "period": period,
                "source": source,
                "confidence": "high",
                "extractors": ["xbrl"],
                "segment_label": name,
            }
        )
        edges.append(
            {
                "subject": sid,
                "subject_type": "Segment",
                "predicate": "IN_SEGMENT",
                "target": entity,
                "target_type": "Company",
                "as_of": as_of,
                "source": source,
                "from_structured": True,
                "extractor": "xbrl",
                "evidence": f"XBRL reportable segment: {name}",
            }
        )

    return facts, edges


# ---------------------------------------------------------------------------
# Live extraction layer (edgartools imports kept local to avoid hard dep in tests)
# ---------------------------------------------------------------------------

def _derive_period_label(xbrl_obj, form: str) -> str:
    """Derive a human-readable period label from an XBRL object.

    Strategy:
    - For 10-K: "FY{year}" where year = calendar year of period_of_report.
      (Companies like NVIDIA have a Jan fiscal year-end, so the period_of_report
      year IS the fiscal year label.)
    - For 10-Q: derive from the fiscal_period / fiscal_year fields of the primary
      revenue fact; fall back to calendar-quarter heuristic.
    """
    period_str = str(xbrl_obj.period_of_report)  # e.g. "2026-01-25"
    year = int(period_str[:4])

    if "10-K" in form:
        return f"FY{year}"

    # 10-Q path: try to get fiscal quarter from facts metadata
    try:
        rev_df = xbrl_obj.facts.get_facts_by_concept("us-gaap:Revenues")
        non_dim = rev_df[rev_df["is_dimensioned"] == False]
        primary = non_dim[non_dim["period_end"].astype(str) == period_str]
        if not primary.empty:
            fp = primary.iloc[0].get("fiscal_period", "")
            fy = primary.iloc[0].get("fiscal_year", year)
            if fp in ("Q1", "Q2", "Q3"):
                q = fp[1]  # "1", "2", "3"
                return f"Q{q}FY{fy}"
    except Exception:
        pass

    # Fallback: calendar quarter
    month = int(period_str[5:7])
    q = (month - 1) // 3 + 1
    return f"Q{q}FY{year}"


def extract(raw: dict) -> tuple[list, list]:
    """Pull XBRL financials from SEC EDGAR for the filing in *raw*.

    raw is a record from raw/sec/ with keys: source_id, accession, form, as_of.

    Returns (facts, edges) via to_facts_edges after pulling:
    - Total revenue: us-gaap:Revenues (non-dimensioned, primary period)
    - Segment revenues: us-gaap:Revenues facts whose context has
      us-gaap:StatementBusinessSegmentsAxis, filtered to primary period_end.

    Segment member terse labels (e.g. "Compute & Networking", "Graphics") are
    looked up from the XBRL element catalog and passed through normalize_surface
    so alias_map resolution applies (decision G10).
    """
    import edgar  # edgartools 5.x

    edgar.set_identity("thrunow@gmail.com")

    accession = raw["accession"]
    filing = edgar.get_by_accession_number(accession)
    xbrl = filing.xbrl()

    period_str = str(xbrl.period_of_report)  # e.g. "2026-01-25"
    period_label = _derive_period_label(xbrl, raw.get("form", filing.form))
    source_id = raw["source_id"]
    as_of = raw["as_of"]
    entity = _entity_from_source(source_id)  # e.g. "nvda-10k-2026-02-25" -> "nvda"

    # --- Total revenue ---
    rev_df = xbrl.facts.get_facts_by_concept("us-gaap:Revenues")
    if rev_df.empty or "is_dimensioned" not in rev_df.columns:
        raise ValueError(f"no XBRL revenue facts in {raw['source_id']}")
    non_dim = rev_df[rev_df["is_dimensioned"] == False]
    primary_rev = non_dim[non_dim["period_end"].astype(str) == period_str]
    if primary_rev.empty:
        raise ValueError(
            f"No non-dimensioned us-gaap:Revenues fact for period {period_str}"
        )
    total_revenue = int(primary_rev.iloc[0]["numeric_value"])

    # --- Segment revenues ---
    contexts = xbrl.contexts
    catalog = xbrl.element_catalog

    # Build map: context_id -> terse segment label, for primary period only
    seg_ctx_label: dict[str, str] = {}
    for ctx_id, ctx in contexts.items():
        dims = ctx.dimensions
        for dim_key, dim_val in dims.items():
            if "StatementBusinessSegments" not in dim_key:
                continue
            end_date = ctx.period.get("endDate", "")
            if end_date != period_str:
                continue
            # Resolve member to a terse human-readable label
            member_key = dim_val.replace(":", "_")
            entry = catalog.get(member_key)
            if entry:
                label = entry.labels.get(_TERSE) or entry.labels.get(_LABEL, dim_val)
            else:
                label = dim_val
            seg_ctx_label[ctx_id] = label

    # Pull revenue facts for those contexts
    all_dim_df = xbrl.facts.get_facts_with_dimensions()
    seg_rev_df = all_dim_df[
        (all_dim_df["concept"] == "us-gaap:Revenues")
        & (all_dim_df["context_ref"].isin(seg_ctx_label))
    ]

    # Build segments dict: label -> value (deduplicate by taking first occurrence per label)
    seen: set[str] = set()
    segments: dict[str, int] = {}
    for _, row in seg_rev_df.iterrows():
        ctx_id = row["context_ref"]
        label = seg_ctx_label[ctx_id]
        if label not in seen:
            seen.add(label)
            segments[label] = int(row["numeric_value"])

    fin = {"revenue": total_revenue, "segments": segments}
    return to_facts_edges(fin, entity=entity, period=period_label, source=source_id, as_of=as_of)


def _entity_from_source(source_id: str) -> str:
    """Extract the entity ticker prefix from a source_id like 'nvda-10k-2026-02-25'."""
    # Normalise: nvda -> nvidia via alias_map, else return ticker as-is
    ticker = source_id.split("-")[0]
    # Use normalize_surface to look up the canonical id
    cid, known = normalize_surface(ticker)
    if known:
        return cid
    return ticker
