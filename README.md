# ComAtlas

**ComAtlas** (Company + Atlas) is an open, source-traceable knowledge graph and wiki of the NVIDIA supply chain — maintained by a Claude Code agent under strict schema and provenance constraints.

Every relation in the graph links back to its original SEC filing, with an honest confidence score and a named extractor. No investment advice is generated or implied.

**Live site:** https://comatlas.kinthai.ai

> **Disclaimer:** ComAtlas presents source-traceable public facts for research and information purposes only. It does **not** constitute investment advice, and nothing on this site should be interpreted as a recommendation to buy or sell any security.

---

## What's in the graph (M1 — current)

The current graph is **NVIDIA-centric**, seeded primarily from the NVIDIA FY2026 Annual Report (10-K, filed 2026-02-25) and the Q1 FY2027 10-Q (filed 2026-05-20). It covers:

- **35 entity pages** across 7 entity types (Company, Product, Chip, Fab, Segment, Technology, DataCenter)
- **~32 published relations**: 25 human-verified gold edges (FY2026 10-K), 5 Claude-anchor edges (10-Q: Blackwell/Spectrum-X IN_SEGMENT), 2 XBRL segment edges
- **Revenue facts**: FY2026 $215.9B total; Compute & Networking $193.5B; Graphics $22.5B

Coverage is intentionally narrow and honest. The M2 roadmap will expand coverage via cross-vendor voting, Wikidata, and automated maintenance cycles.

---

## Architecture

```
SEC EDGAR                      graph.json
    │                               │
    ▼                               ▼
fetch_sources.py  →  raw/sec/   web/graph/
    │                               │
    ▼                               ▼
extract_consensus.py            Quartz build
  ├─ anchor_claude.py  (claude -p subscription)
  └─ leg_xbrl.py       (edgartools)
    │
    ▼
normalize.py  (alias_map → canonical entity ids)
    │
    ▼
score_m1  (structured=high, narrative=medium)
    │
    ▼
update_content.py  (merge edges/facts → content/entities/*.md)
    │
    ▼
lint_frontmatter.py  (schema + red-line enforcement; exit 1 on any violation)
    │
    ▼
build_graph.js  →  public/graph/graph.json
    │
    ▼
npx quartz build  →  public/  →  GitHub Pages
```

**Markdown as single source of truth.** `content/entities/*.md` frontmatter is the authoritative store for all relations and facts. The pipeline reads and writes only this layer; the graph and the rendered wiki are both derived artifacts.

**graph.json contract.** `build_graph.js` emits a library-agnostic JSON structure (`{nodes, edges}`) where every edge carries `predicate`, `as_of`, `confidence`, and `source_ref`. Visualization-library-specific fields live in `web/graph/adapters/` — not in graph.json.

---

## Repo layout

```
/
├─ CNAME                          # comatlas.kinthai.ai (do not touch)
├─ CLAUDE.md                      # Maintainer agent rules (this file is the law)
├─ content/
│  ├─ index.md                    # Homepage
│  ├─ disclaimer.md
│  ├─ entities/<id>.md            # Entity pages (schema-enforced frontmatter)
│  └─ sources/<source-id>.md      # Source provenance pages
├─ ontology/
│  ├─ entity_types.yml            # Closed set of 8 entity types (human-only edits)
│  ├─ predicates.yml              # Closed set of 8 predicates + domain/range (human-only)
│  └─ alias_map.yml               # Entity resolution surface → canonical id
├─ raw/
│  ├─ _state.json                 # Incremental ingestion state
│  └─ sec/<source-id>.json        # Raw SEC filing sections (public domain)
├─ scripts/
│  ├─ fetch_sources.py            # EDGAR incremental ingest
│  ├─ extract_consensus.py        # Pipeline entry point (Claude anchor + XBRL)
│  ├─ extract/
│  │  ├─ anchor_claude.py         # Claude anchor leg (M1)
│  │  ├─ leg_xbrl.py              # XBRL deterministic leg (M1)
│  │  ├─ second_minimax.py        # MiniMax second vote (M2, not yet active)
│  │  ├─ leg_glirel.py            # GLiREL corroboration (M2, not yet active)
│  │  └─ leg_wikidata.py          # Wikidata structural (M2, not yet active)
│  ├─ consensus.py                # Voting + scoring (M2; M1 uses score_m1)
│  ├─ update_content.py           # Merge edges/facts into frontmatter
│  ├─ lint_frontmatter.py         # Red-line guardian
│  ├─ normalize.py                # Surface → canonical id via alias_map
│  ├─ ontology.py                 # Ontology loaders
│  └─ build_graph.js              # frontmatter → graph.json
├─ web/graph/
│  ├─ index.html  app.js  datalayer.js
│  └─ adapters/forcegraph.js
├─ eval/
│  ├─ gold_triples.json           # Human-verified gold set (do not modify)
│  ├─ alias_gold.json
│  └─ run_eval.py                 # AC-1/AC-2/AC-4 acceptance metrics
├─ tests/
│  ├─ *.py                        # pytest unit tests
│  └─ web/*.test.mjs              # Node --test integration tests
└─ .github/workflows/
   ├─ deploy.yml                  # push → test → build → Pages
   └─ maintain.yml                # daily cron (M2; not yet active)
```

---

## Local development

**Requirements:** Python 3.12+, Node 22+.

```bash
# Python environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Node dependencies (Quartz)
npm ci

# Run the pipeline
python scripts/fetch_sources.py            # pull new filings from EDGAR
python scripts/extract_consensus.py        # extract + update content/
python scripts/lint_frontmatter.py         # validate schema (exit 0 = clean)
node scripts/build_graph.js               # regenerate graph.json

# Build and serve locally
npx quartz build --serve

# Tests
pytest -q                                  # 74 Python unit tests
node --test tests/web/*.test.mjs           # 8 Node integration tests
python eval/run_eval.py                    # AC-1/2/4 acceptance metrics
```

**Claude anchor note:** `extract_consensus.py` calls `claude -p` (headless Claude Code subscription). Avoid running heavy extraction concurrently with other active Claude sessions — they share the same subscription quota.

---

## Ontology

**Entity types (8):** `Company` `Product` `Chip` `Fab` `DataCenter` `Technology` `Person` `Segment`

**Predicates (8 active):**

| Predicate | Domain | Range | Notes |
|---|---|---|---|
| `SUPPLIES` | Company, Fab | Company | inverse: CUSTOMER_OF |
| `CUSTOMER_OF` | Company | Company, Fab | inverse: SUPPLIES |
| `COMPETES_WITH` | Company, Product, Chip | Company, Product, Chip | symmetric |
| `MANUFACTURED_BY` | Product, Chip, Company | Fab, Company | functional when subject=Chip (G12) |
| `OWNS_STAKE_IN` | Company, Person | Company | |
| `SUBSIDIARY_OF` | Company | Company | functional (one direct parent) |
| `PARTNER_WITH` | Company | Company | symmetric |
| `IN_SEGMENT` | Segment, Product, Chip | Company, Segment | subject∈segment namespace, G10 |

`HEADQUARTERED_IN` is reserved/disabled (no `Place` entity type exists; headquarters is stored as the scalar `hq:` field instead).

The ontology is a **closed set** — agents must never add types or predicates. New candidates go to the review queue for human decision.

---

## Confidence and publish gate

| Level | Meaning | Published? |
|---|---|---|
| `high` | Structured source (XBRL) or ≥2 extractors in agreement across ≥2 sources | Yes |
| `medium` | Single source or single extractor vote | Yes (body notes unverified) |
| `low` | Conflict, grounding failure, or weak support | No — review queue only |

`lint_frontmatter.py` enforces this: a `low`-confidence page with `publish: true` is a **hard error** (red line #3).

---

## Provenance honesty

Every relation has an `extractors` list drawn from: `claude`, `minimax`, `glirel`, `xbrl`, `human`, `wikidata`.

`human` means a human manually verified or seeded the edge. It must never be relabeled as an LLM extractor, and LLM-extracted edges must never be labeled `human`. Provenance honesty is a hard red line (see `CLAUDE.md §11` red line #8).

---

## Status

**M1 — shipped (June 2026)**
- Claude anchor (headless `claude -p`, subscription auth) + XBRL deterministic leg
- 35 entity pages, ~32 published edges, revenue facts FY2026 + Q1 FY2027
- 74 pytest + 8 Node tests; AC-1/AC-2/AC-4 all 1.000
- Deployed on GitHub Pages at https://comatlas.kinthai.ai

**M2 — planned**
- MiniMax M3 as second vote; GLiREL corroboration; Wikidata structural relations
- Full consensus voting with grounding evidence checks
- `maintain.yml` daily cron for automated incremental updates
- Review queue surfacing for human resolution of conflicts
- Expanded entity coverage beyond NVIDIA core supply chain
