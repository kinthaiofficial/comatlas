---
aliases:
- nvidia
confidence: medium
facts:
- confidence: high
  extractors:
  - xbrl
  metric: revenue
  period: Q1FY2027
  source: nvda-10q-2026-05-20
  unit: USD
  value: 81615000000
- confidence: high
  extractors:
  - xbrl
  metric: segment_revenue:nvidia-compute-networking
  period: Q1FY2027
  source: nvda-10q-2026-05-20
  unit: USD
  value: 74550000000
- confidence: high
  extractors:
  - xbrl
  metric: segment_revenue:nvidia-graphics
  period: Q1FY2027
  source: nvda-10q-2026-05-20
  unit: USD
  value: 7065000000
- confidence: high
  extractors:
  - xbrl
  metric: revenue
  period: FY2026
  source: nvda-10k-2026-02-25
  unit: USD
  value: 215938000000
- confidence: high
  extractors:
  - xbrl
  metric: segment_revenue:nvidia-compute-networking
  period: FY2026
  source: nvda-10k-2026-02-25
  unit: USD
  value: 193479000000
- confidence: high
  extractors:
  - xbrl
  metric: segment_revenue:nvidia-graphics
  period: FY2026
  source: nvda-10k-2026-02-25
  unit: USD
  value: 22459000000
id: nvidia
label: nvidia
last_updated: '2026-06-11'
publish: true
relations:
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: MANUFACTURED_BY
  source: nvda-10k-2026-02-25
  target: tsmc
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: MANUFACTURED_BY
  source: nvda-10k-2026-02-25
  target: samsung
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: amd
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: intel
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: huawei
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: microsoft
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: amazon
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: alphabet
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: broadcom
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: qualcomm
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: tesla
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: alibaba
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: arista
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: cisco
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: hpe
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: marvell
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: renesas
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  - human
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: baidu
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: ambarella
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: samsung
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  predicate: COMPETES_WITH
  source: nvda-10k-2026-02-25
  target: lumentum
- as_of: 2026-Q1
  confidence: medium
  corroborates: []
  extractors:
  - claude
  predicate: PARTNER_WITH
  source: nvda-10k-2026-02-25
  target: groq
sources:
- nvda-10k-2026-02-25
- nvda-10q-2026-05-20
type: Company
---

<!-- AUTO-RELATIONS:BEGIN -->
| relation | target | as of | confidence | source |
|---|---|---|---|---|
| MANUFACTURED_BY | [[tsmc]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| MANUFACTURED_BY | [[samsung]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[amd]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[intel]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[huawei]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[microsoft]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[amazon]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[alphabet]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[broadcom]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[qualcomm]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[tesla]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[alibaba]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[arista]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[cisco]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[hpe]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[marvell]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[renesas]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[baidu]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[ambarella]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[samsung]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| COMPETES_WITH | [[lumentum]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| PARTNER_WITH | [[groq]] | 2026-Q1 | medium | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |

| metric | value | period | source |
|---|---|---|---|
| revenue | 81,615,000,000 USD | Q1FY2027 | [[sources/nvda-10q-2026-05-20|nvda-10q-2026-05-20]] |
| segment_revenue:nvidia-compute-networking | 74,550,000,000 USD | Q1FY2027 | [[sources/nvda-10q-2026-05-20|nvda-10q-2026-05-20]] |
| segment_revenue:nvidia-graphics | 7,065,000,000 USD | Q1FY2027 | [[sources/nvda-10q-2026-05-20|nvda-10q-2026-05-20]] |
| revenue | 215,938,000,000 USD | FY2026 | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| segment_revenue:nvidia-compute-networking | 193,479,000,000 USD | FY2026 | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
| segment_revenue:nvidia-graphics | 22,459,000,000 USD | FY2026 | [[sources/nvda-10k-2026-02-25|nvda-10k-2026-02-25]] |
<!-- AUTO-RELATIONS:END -->
