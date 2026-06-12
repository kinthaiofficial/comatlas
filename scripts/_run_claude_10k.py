#!/usr/bin/env python3
"""One-shot driver: apply the Claude (interactive Claude Code) anchor extraction of the
FY2026 10-K to the pipeline WITHOUT shelling out to `claude -p` (which contends with this
same Claude Code session for the subscription quota).

The triples below were extracted by Claude reading raw/sec/nvda-10k-2026-02-25.json directly,
constrained to the closed ontology. Provenance is honestly `claude`. Evidence sentences are
verbatim from the filing and verified as substrings before the run.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = "nvda-10k-2026-02-25"
AS_OF = "2026-Q1"

# Verbatim evidence blocks (each a substring of the filing text)
EV_FOUNDRY = ("We utilize foundries, such as Taiwan Semiconductor Manufacturing Company Limited, or TSMC, "
              "and Samsung Electronics Co., Ltd., or Samsung, to produce our semiconductor wafers.")
EV_MEMORY = "We purchase memory from SK Hynix Inc., Micron Technology, Inc., and Samsung."
EV_ASSEMBLY = ("We engage with independent subcontractors and contract manufacturers such as Hon Hai Precision "
               "Industry Co., Ltd., Wistron Corporation, and Fabrinet to perform assembly, testing and packaging "
               "of our final products.")
EV_COMP_GPU = ("such as Advanced Micro Devices, Inc., or AMD, Huawei Technologies Co. Ltd., or Huawei, and Intel "
               "Corporation, or Intel;")
EV_COMP_CLOUD = ("such as Alibaba Group, Alphabet Inc., Amazon, Inc., or Amazon, Baidu, Inc., Huawei, and "
                 "Microsoft Corporation, or Microsoft;")
EV_COMP_SOC = ("such as Ambarella, Inc., AMD, Broadcom, Intel, Qualcomm Incorporated, Renesas Electronics "
               "Corporation, and Samsung, or companies with internal teams designing SoC products for their own "
               "products and services, such as Tesla, Inc.")
EV_COMP_NET = ("such as AMD, Arista Networks, Broadcom, Cisco Systems, Inc., Hewlett Packard Enterprise Company, "
               "Huawei, Intel, Lumentum Holdings Inc., and Marvell Technology, Inc, as well as internal teams of "
               "system vendors and large cloud services companies.")
EV_MELLANOX = ("Our acquisition of Mellanox in 2020 expanded our offerings to include networking, enabled our "
               "platforms to be data center scale, and led to the introduction of a new processor class")
EV_SEG_CN = ("The Compute & Networking segment includes our Data Center accelerated computing and networking "
             "platforms and AI solutions and software, and Automotive platforms and autonomous and electric "
             "vehicle solutions including software.")
EV_SEG_GFX = ("The Graphics segment includes GeForce GPUs for gaming and PCs, and Quadro/NVIDIA RTX GPUs for "
              "enterprise workstation graphics.")
EV_GROQ = "execution of a non-exclusive license agreement with Groq"

CO = "Company"

def t(subj, stype, pred, obj, otype, ev):
    return {"subject": subj, "subject_type": stype, "predicate": pred, "object": obj,
            "object_type": otype, "evidence": ev, "as_of": AS_OF,
            "source": SRC, "extractor": "claude"}

TRIPLES = [
    # MANUFACTURED_BY (foundries) — range allows Company; tsmc/samsung pages are type Company
    t("NVIDIA", CO, "MANUFACTURED_BY", "TSMC", CO, EV_FOUNDRY),
    t("NVIDIA", CO, "MANUFACTURED_BY", "Samsung", CO, EV_FOUNDRY),
    # SUPPLIES — memory
    t("SK Hynix Inc.", CO, "SUPPLIES", "NVIDIA", CO, EV_MEMORY),
    t("Micron Technology, Inc.", CO, "SUPPLIES", "NVIDIA", CO, EV_MEMORY),
    t("Samsung", CO, "SUPPLIES", "NVIDIA", CO, EV_MEMORY),
    # SUPPLIES — assembly/test/packaging
    t("Hon Hai Precision Industry Co., Ltd.", CO, "SUPPLIES", "NVIDIA", CO, EV_ASSEMBLY),
    t("Wistron Corporation", CO, "SUPPLIES", "NVIDIA", CO, EV_ASSEMBLY),
    t("Fabrinet", CO, "SUPPLIES", "NVIDIA", CO, EV_ASSEMBLY),
    # COMPETES_WITH — GPU / accelerated computing
    t("NVIDIA", CO, "COMPETES_WITH", "AMD", CO, EV_COMP_GPU),
    t("NVIDIA", CO, "COMPETES_WITH", "Huawei", CO, EV_COMP_GPU),
    t("NVIDIA", CO, "COMPETES_WITH", "Intel", CO, EV_COMP_GPU),
    # COMPETES_WITH — cloud internal silicon
    t("NVIDIA", CO, "COMPETES_WITH", "Alibaba Group", CO, EV_COMP_CLOUD),
    t("NVIDIA", CO, "COMPETES_WITH", "Alphabet Inc.", CO, EV_COMP_CLOUD),
    t("NVIDIA", CO, "COMPETES_WITH", "Amazon", CO, EV_COMP_CLOUD),
    t("NVIDIA", CO, "COMPETES_WITH", "Baidu, Inc.", CO, EV_COMP_CLOUD),
    t("NVIDIA", CO, "COMPETES_WITH", "Microsoft", CO, EV_COMP_CLOUD),
    # COMPETES_WITH — SoC
    t("NVIDIA", CO, "COMPETES_WITH", "Ambarella, Inc.", CO, EV_COMP_SOC),
    t("NVIDIA", CO, "COMPETES_WITH", "Broadcom", CO, EV_COMP_SOC),
    t("NVIDIA", CO, "COMPETES_WITH", "Qualcomm Incorporated", CO, EV_COMP_SOC),
    t("NVIDIA", CO, "COMPETES_WITH", "Renesas Electronics Corporation", CO, EV_COMP_SOC),
    t("NVIDIA", CO, "COMPETES_WITH", "Samsung", CO, EV_COMP_SOC),
    t("NVIDIA", CO, "COMPETES_WITH", "Tesla, Inc.", CO, EV_COMP_SOC),
    # COMPETES_WITH — networking
    t("NVIDIA", CO, "COMPETES_WITH", "Arista Networks", CO, EV_COMP_NET),
    t("NVIDIA", CO, "COMPETES_WITH", "Cisco Systems, Inc.", CO, EV_COMP_NET),
    t("NVIDIA", CO, "COMPETES_WITH", "Hewlett Packard Enterprise Company", CO, EV_COMP_NET),
    t("NVIDIA", CO, "COMPETES_WITH", "Lumentum Holdings Inc.", CO, EV_COMP_NET),
    t("NVIDIA", CO, "COMPETES_WITH", "Marvell Technology, Inc", CO, EV_COMP_NET),
    # SUBSIDIARY_OF
    t("Mellanox", CO, "SUBSIDIARY_OF", "NVIDIA", CO, EV_MELLANOX),
    # IN_SEGMENT (Segment -> Company)
    t("Compute & Networking", "Segment", "IN_SEGMENT", "NVIDIA", CO, EV_SEG_CN),
    t("Graphics", "Segment", "IN_SEGMENT", "NVIDIA", CO, EV_SEG_GFX),
    # PARTNER_WITH — Groq IP license
    t("NVIDIA", CO, "PARTNER_WITH", "Groq, Inc.", CO, EV_GROQ),
]


def main():
    raw = json.loads((ROOT / "raw" / "sec" / f"{SRC}.json").read_text())
    fulltext = "\n".join(raw["sections"].values())
    # Verify every evidence sentence is verbatim in the filing
    bad = [tr for tr in TRIPLES if tr["evidence"] not in fulltext]
    if bad:
        for tr in bad:
            print(f"EVIDENCE NOT VERBATIM: {tr['subject']} {tr['predicate']} {tr['object']}\n  {tr['evidence']!r}",
                  file=sys.stderr)
        sys.exit(2)
    print(f"evidence verbatim OK for all {len(TRIPLES)} triples", file=sys.stderr)

    from scripts.extract import anchor_claude
    from scripts import extract_consensus
    anchor_claude.extract_source = lambda raw, runner=None, checkpoint_dir=None: list(TRIPLES)
    done = extract_consensus.run()
    print(json.dumps({"processed": done}))


if __name__ == "__main__":
    main()
