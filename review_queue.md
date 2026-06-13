# Review queue

Low-confidence and conflicting edges for human review. The maintenance agent writes here but never decides — you do. Resolve by editing `content/` and removing the block.

> **2026-06-13 triage (in-session maintenance).** None of the items below ever entered the
> graph (the anchor-gate keeps weak-model-only edges out). After review, 32 items were dismissed
> as second-vote (MiniMax) noise and 3 are kept below for human verification. Full pre-triage
> list is in git history.

## ⚠️ Needs human verification (real-world events; not confirmed by an anchor in current sources)

<!-- RQ:verify:nvidia:OWNS_STAKE_IN:openai -->
### nvidia OWNS_STAKE_IN openai · nvidia PARTNER_WITH openai
The FY2026 10-K describes an OpenAI investment-and-partnership agreement as **being finalized,
with no assurance it will be completed** — so it was intentionally not published. Promote (with a
`source`) only once a filing confirms the deal closed.

<!-- RQ:verify:nvidia:OWNS_STAKE_IN:intel -->
### nvidia OWNS_STAKE_IN intel
Proposed by the MiniMax second vote only; **not confirmed by an anchor in the current sources**
(no grounded evidence in the FY2026 10-K). A NVIDIA–Intel investment was reported in the news —
verify against a primary filing before adding, with that filing as `source`.

## Dismissed 2026-06-13 (MiniMax-only over-extraction — kept out of the graph by the anchor-gate)

- **Product/category phrases treated as entities** (IN_SEGMENT / MANUFACTURED_BY): geforce-gpus,
  quadro-nvidia-rtx-gpus, geforce-rtx-gpus, geforce-now, nvidia-blackwell-geforce-rtx-50-series,
  nvidia-rtx-pro-gpus, nvidia-ai-enterprise, nvidia-vgpu-software, blackwell-architecture,
  blackwell-computing-platform, data-center-accelerated-computing-and-networking-platforms,
  automotive-platforms — plus invented segments "gaming" / "professional-visualization". Not entities.
- **Generic groups treated as entities**: nvidia SUPPLIES major-server-makers-and-csps;
  nvidia PARTNER_WITH automotive-oems / independent-software-vendors / universities-and-startups /
  automotive-ecosystem-partners. Not specific entities.
- **PARTNER_WITH redundant with existing supply edges**: nvidia PARTNER_WITH tsmc / samsung /
  sk-hynix / micron / hon-hai / wistron / fabrinet — already modeled as SUPPLIES / MANUFACTURED_BY.
- **Direction-redundant / governance misread**: groq PARTNER_WITH nvidia (inverse of the published
  nvidia↔groq edge; PARTNER_WITH is symmetric); nvidia PARTNER_WITH microsoft (a change-of-control
  clause, not a supply-chain partnership).
- **1 grounding false-negative** (low): nvidia COMPETES_WITH qualcomm — qualcomm is already
  published as a medium competitor (the edge kept its confidence via merge raise-only).
