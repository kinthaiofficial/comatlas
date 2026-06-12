#!/usr/bin/env python3
"""One-shot: recompute the FY2026 10-K under the M2a consensus pipeline.

Anchor = the in-session Claude triples (injected, no claude -p contention); second vote +
grounding = real MiniMax M3. Demonstrates M2a on real data: agreeing edges gain `minimax` in
extractors; unsupported edges are grounded-out to `low` and pushed to review_queue.md.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import extract_consensus as pipe
from scripts.extract import anchor_claude
from scripts._run_claude_10k import TRIPLES   # the 31 in-session Claude triples (audit record)

SID = "nvda-10k-2026-02-25"


def main():
    state_path = ROOT / "raw" / "_state.json"
    state = json.loads(state_path.read_text())
    state[SID]["processed"] = False
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True))

    # Inject in-session Claude anchor (avoids claude -p quota contention); MiniMax legs run for real.
    anchor_claude.extract_source = lambda raw, runner=None, checkpoint_dir=None: list(TRIPLES)
    done = pipe.run()
    print(json.dumps({"processed": done}))


if __name__ == "__main__":
    main()
