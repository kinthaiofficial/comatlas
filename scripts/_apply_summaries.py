#!/usr/bin/env python3
"""One-shot: apply Claude-authored neutral entity summaries (no claude -p subprocess).

Each summary is original paraphrase (not copied text, red line #5), grounded in NVIDIA's
FY2026 Form 10-K, and contains no investment advice (red line #6). Kept as an audit record.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import update_content

CONTENT = ROOT / "content"
TODAY = "2026-06-12"
SRC = {"id": "nvda-10k-2026-02-25", "kind": "sec-filing",
       "title": "NVIDIA FY2026 Form 10-K",
       "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125",
       "date": "2026-02-25"}

# eid -> neutral, sourced, paraphrased summary (2-4 sentences). Source: FY2026 10-K.
SUMMARIES = {
    "nvidia": (
        "NVIDIA is an accelerated-computing and AI-infrastructure company; per its FY2026 Form 10-K "
        "it reported about $215.9B in revenue across two operating segments, Compute & Networking and "
        "Graphics. It follows a fabless model, designing chips and systems while outsourcing wafer "
        "fabrication and assembly to third parties. Relationships below are drawn from that filing."
    ),
    "nvidia-compute-networking": (
        "Compute & Networking is one of NVIDIA's two reported operating segments, covering its data-center "
        "accelerated-computing and networking platforms plus automotive solutions. Per the FY2026 10-K it "
        "accounted for roughly $193.5B of segment revenue."
    ),
    "nvidia-graphics": (
        "Graphics is one of NVIDIA's two reported operating segments, covering GeForce GPUs for gaming and PCs "
        "and RTX GPUs for professional workstations. Per the FY2026 10-K it accounted for roughly $22.5B of "
        "segment revenue."
    ),
    "tsmc": (
        "Taiwan Semiconductor Manufacturing Company (TSMC) is a contract chip foundry. NVIDIA's FY2026 10-K "
        "lists TSMC among the foundries it uses to produce its semiconductor wafers, reflecting NVIDIA's "
        "fabless manufacturing strategy."
    ),
    "samsung": (
        "Samsung Electronics appears in NVIDIA's FY2026 10-K in several roles: as a foundry that produces "
        "NVIDIA's semiconductor wafers, as a memory supplier, and among the companies NVIDIA names as "
        "competitors in SoC products — an example of supplier-competitor overlap common in the industry."
    ),
    "sk-hynix": (
        "SK Hynix is a memory manufacturer. NVIDIA's FY2026 10-K names it among the suppliers from which "
        "NVIDIA purchases memory used in its products."
    ),
    "micron": (
        "Micron Technology is a memory manufacturer. NVIDIA's FY2026 10-K names it among the suppliers from "
        "which NVIDIA purchases memory."
    ),
    "hon-hai": (
        "Hon Hai Precision Industry (Foxconn) is a contract manufacturer. NVIDIA's FY2026 10-K lists it among "
        "the subcontractors that perform assembly, testing and packaging of NVIDIA's final products."
    ),
    "wistron": (
        "Wistron Corporation is a contract manufacturer. NVIDIA's FY2026 10-K lists it among the subcontractors "
        "performing assembly, testing and packaging of NVIDIA's final products."
    ),
    "fabrinet": (
        "Fabrinet is a contract manufacturer of advanced products. NVIDIA's FY2026 10-K lists it among the "
        "subcontractors performing assembly, testing and packaging of NVIDIA's final products."
    ),
    "mellanox": (
        "Mellanox Technologies is a networking company NVIDIA acquired in 2020; per the FY2026 10-K the deal "
        "added networking to NVIDIA's portfolio and introduced the data processing unit (DPU). It is now a "
        "subsidiary of NVIDIA."
    ),
    "groq": (
        "Groq is an AI-chip company. NVIDIA's FY2026 10-K discloses that NVIDIA executed a non-exclusive "
        "intellectual-property license agreement with Groq during the fiscal year."
    ),
    "amd": (
        "Advanced Micro Devices (AMD) designs CPUs and GPUs. NVIDIA's FY2026 10-K names AMD among its "
        "competitors in GPUs and accelerated-computing solutions, as well as in SoC and networking products."
    ),
    "intel": (
        "Intel is a semiconductor company. NVIDIA's FY2026 10-K names Intel among its competitors across GPUs, "
        "accelerated computing, SoCs and networking products."
    ),
    "huawei": (
        "Huawei is a technology and telecommunications company. NVIDIA's FY2026 10-K names it among NVIDIA's "
        "competitors in accelerated computing, internal-silicon cloud solutions and networking."
    ),
    "broadcom": (
        "Broadcom is a semiconductor and infrastructure-software company. NVIDIA's FY2026 10-K names it among "
        "NVIDIA's competitors in SoC and networking products."
    ),
    "qualcomm": (
        "Qualcomm designs SoCs for mobile and embedded devices. NVIDIA's FY2026 10-K names it among NVIDIA's "
        "competitors in SoC products used in servers, automobiles, autonomous machines and gaming devices."
    ),
    "renesas": (
        "Renesas Electronics is a semiconductor maker focused on embedded and automotive chips. NVIDIA's "
        "FY2026 10-K names it among NVIDIA's competitors in SoC products."
    ),
    "ambarella": (
        "Ambarella designs SoCs for computer-vision applications. NVIDIA's FY2026 10-K names it among NVIDIA's "
        "competitors in SoC products."
    ),
    "tesla": (
        "Tesla designs SoCs internally for its own products. NVIDIA's FY2026 10-K cites it as an example of a "
        "company with internal teams designing SoC products, listing it among NVIDIA's competitors in that area."
    ),
    "arista": (
        "Arista Networks builds data-center networking switches. NVIDIA's FY2026 10-K names it among NVIDIA's "
        "competitors in networking products."
    ),
    "cisco": (
        "Cisco Systems is a networking-equipment company. NVIDIA's FY2026 10-K names it among NVIDIA's "
        "competitors in networking products."
    ),
    "hpe": (
        "Hewlett Packard Enterprise provides servers and networking. NVIDIA's FY2026 10-K names it among "
        "NVIDIA's competitors in networking products."
    ),
    "lumentum": (
        "Lumentum Holdings makes optical components including modules used in networking. NVIDIA's FY2026 10-K "
        "names it among NVIDIA's competitors in networking products."
    ),
    "marvell": (
        "Marvell Technology designs data-infrastructure semiconductors. NVIDIA's FY2026 10-K names it among "
        "NVIDIA's competitors in networking products."
    ),
    "microsoft": (
        "Microsoft is a cloud-services company. NVIDIA's FY2026 10-K names it among large cloud providers whose "
        "internal hardware/software efforts make them NVIDIA competitors, and notes it also supplies Arm-based "
        "CPU efforts in that context."
    ),
    "amazon": (
        "Amazon operates large cloud services. NVIDIA's FY2026 10-K names it among cloud providers with internal "
        "silicon efforts that compete with NVIDIA, including in Arm-based CPUs."
    ),
    "alphabet": (
        "Alphabet (Google) operates large cloud services. NVIDIA's FY2026 10-K names it among cloud providers "
        "whose internal hardware/software efforts make them NVIDIA competitors."
    ),
    "alibaba": (
        "Alibaba Group operates cloud services. NVIDIA's FY2026 10-K names it among cloud providers with internal "
        "silicon efforts that compete with NVIDIA."
    ),
    "baidu": (
        "Baidu operates cloud and AI services. NVIDIA's FY2026 10-K names it among cloud providers with internal "
        "silicon efforts that compete with NVIDIA."
    ),
}

if __name__ == "__main__":
    pending = {k: v for k, v in SUMMARIES.items() if v and v.strip()}
    update_content.apply(CONTENT, edges=[], facts=[], source_meta=SRC, today=TODAY, summaries=pending)
    print(f"applied {len(pending)} summaries")
