---
aliases:
- nvidia-graphics
confidence: medium
id: nvidia-graphics
label: nvidia-graphics
last_updated: '2026-06-12'
publish: true
relations:
- as_of: 2026-Q2
  confidence: high
  corroborates:
  - nvda-10q-2026-05-20
  extractors:
  - claude
  - xbrl
  predicate: IN_SEGMENT
  source: nvda-10k-2026-02-25
  target: nvidia
sources:
- nvda-10k-2026-02-25
- nvda-10q-2026-05-20
summary_by: claude
type: Segment
---

<!-- SUMMARY:BEGIN -->
Graphics is one of NVIDIA's two reported operating segments, covering GeForce GPUs for gaming and PCs and RTX GPUs for professional workstations. Per the FY2026 10-K it accounted for roughly $22.5B of segment revenue.
<!-- SUMMARY:END -->

<!-- AUTO-RELATIONS:BEGIN -->
| relation | target | as of | confidence | basis | source |
|---|---|---|---|---|---|
| IN_SEGMENT | [[nvidia]] | 2026-Q2 | high |  | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
<!-- AUTO-RELATIONS:END -->
