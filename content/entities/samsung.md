---
aliases:
- samsung
confidence: medium
id: samsung
label: samsung
last_updated: '2026-06-12'
publish: true
relations:
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: SUPPLIES
  quote: We purchase memory from SK Hynix Inc., Micron Technology, Inc., and Samsung.
  source: nvda-10k-2026-02-25
  target: nvidia
sources:
- nvda-10k-2026-02-25
summary_by: claude
type: Company
---

<!-- SUMMARY:BEGIN -->
Samsung Electronics appears in NVIDIA's FY2026 10-K in several roles: as a foundry that produces NVIDIA's semiconductor wafers, as a memory supplier, and among the companies NVIDIA names as competitors in SoC products — an example of supplier-competitor overlap common in the industry.
<!-- SUMMARY:END -->

<!-- AUTO-RELATIONS:BEGIN -->
| relation | target | as of | confidence | basis | source |
|---|---|---|---|---|---|
| SUPPLIES | [[nvidia]] | 2026-Q1 | medium | <a href="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm#:~:text=We%20purchase%20memory%20from%20SK%20Hynix%20Inc.%2C%20Micron%20Technology%2C%20Inc.%2C%20and%20Samsung." target="_blank" rel="noopener">We purchase memory from SK Hynix Inc., Micron Technology, Inc., and Samsung.</a> | <a href="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm" target="_blank" rel="noopener">nvda-10k-2026-02-25</a> |
<!-- AUTO-RELATIONS:END -->

<!-- INBOUND:BEGIN -->
**Referenced by**

| from | relation | source |
|---|---|---|
| [[nvidia]] | COMPETES_WITH | <a href="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm" target="_blank" rel="noopener">nvda-10k-2026-02-25</a> |
| [[nvidia]] | MANUFACTURED_BY | <a href="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm" target="_blank" rel="noopener">nvda-10k-2026-02-25</a> |
<!-- INBOUND:END -->
