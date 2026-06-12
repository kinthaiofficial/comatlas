from pathlib import Path
import textwrap
from scripts.lint_frontmatter import lint_dir

GOOD_SOURCE = """---\nid: src-1\nkind: sec-filing\ntitle: T\nurl: https://x\ndate: 2026-02-26\npublish: true\n---\n"""

def write(tmp, rel, body):
    p = tmp / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body)); return p

def page(rels="", extra=""):
    return f"""---
type: Company
id: acme
label: Acme
confidence: high
publish: true
last_updated: 2026-06-07
sources: [src-1]
{extra}relations:{rels or " []"}
---
"""

REL_OK = """
  - predicate: SUPPLIES
    target: nvidia
    as_of: 2026-Q1
    source: src-1
    confidence: medium
    extractors: [claude]"""

def setup(tmp, entity_body):
    write(tmp, "content/sources/src-1.md", GOOD_SOURCE)
    write(tmp, "content/entities/nvidia.md", page().replace("acme", "nvidia").replace("Acme", "NVIDIA"))
    write(tmp, "content/entities/acme.md", entity_body)
    return tmp / "content"

def test_clean_pages_pass(tmp_path):
    assert lint_dir(setup(tmp_path, page(REL_OK))) == []

def test_bad_type_rejected(tmp_path):
    errs = lint_dir(setup(tmp_path, page(REL_OK).replace("type: Company", "type: Startup")))
    assert any("not in closed set" in e for e in errs)

def test_relation_missing_source_rejected(tmp_path):
    errs = lint_dir(setup(tmp_path, page(REL_OK.replace("    source: src-1\n", ""))))
    assert any("missing" in e and "source" in e for e in errs)

def test_unresolvable_target_rejected(tmp_path):
    errs = lint_dir(setup(tmp_path, page(REL_OK.replace("target: nvidia", "target: ghost"))))
    assert any("unresolvable" in e for e in errs)

def test_low_page_published_is_red_line(tmp_path):
    errs = lint_dir(setup(tmp_path, page(REL_OK).replace("confidence: high", "confidence: low")))
    assert any("RED LINE" in e for e in errs)

def test_unknown_predicate_rejected(tmp_path):
    errs = lint_dir(setup(tmp_path, page(REL_OK.replace("SUPPLIES", "ACQUIRED"))))
    assert any("predicate" in e for e in errs)

def test_domain_violation_rejected(tmp_path):
    # Person cannot SUPPLIES (domain is Company/Fab)
    errs = lint_dir(setup(tmp_path, page(REL_OK).replace("type: Company", "type: Person")))
    assert any("domain" in e for e in errs)

FACTS_OK = """\
facts:
  - metric: revenue
    value: 1000
    period: 2025-Q4
    source: src-1
    confidence: high
    extractors: [claude]
"""

def test_facts_bad_confidence(tmp_path):
    bad = FACTS_OK.replace("confidence: high", "confidence: uncertain")
    errs = lint_dir(setup(tmp_path, page(REL_OK, extra=bad)))
    assert any("bad confidence" in e for e in errs)

def test_facts_missing_period(tmp_path):
    # Remove the period line
    bad = "\n".join(l for l in FACTS_OK.splitlines() if "period:" not in l) + "\n"
    errs = lint_dir(setup(tmp_path, page(REL_OK, extra=bad)))
    assert any("missing" in e for e in errs)

def test_relation_range_violation(tmp_path):
    # nvidia is type Company; SUPPLIES range is [Company] — use a Chip target instead
    chip_page = page().replace("acme", "mycpu").replace("Acme", "MyCPU").replace("type: Company", "type: Chip")
    write(tmp_path, "content/entities/mycpu.md", chip_page)
    bad_rel = REL_OK.replace("target: nvidia", "target: mycpu")
    errs = lint_dir(setup(tmp_path, page(bad_rel)))
    assert any("range" in e for e in errs)

def test_relation_bad_confidence(tmp_path):
    bad_rel = REL_OK.replace("confidence: medium", "confidence: maybe")
    errs = lint_dir(setup(tmp_path, page(bad_rel)))
    assert any("bad confidence" in e for e in errs)

def test_source_missing_url(tmp_path):
    bad_src = GOOD_SOURCE.replace("url: https://x\n", "")
    write(tmp_path, "content/sources/src-1.md", bad_src)
    write(tmp_path, "content/entities/nvidia.md", page().replace("acme", "nvidia").replace("Acme", "NVIDIA"))
    write(tmp_path, "content/entities/acme.md", page(REL_OK))
    errs = lint_dir(tmp_path / "content")
    assert any("sources/" in e for e in errs)

def test_lint_dir_no_entities_subdir(tmp_path):
    # A tmp dir without entities/ should return [] without crashing
    errs = lint_dir(tmp_path)
    assert errs == []


# ── M2.5 Wiki: quote length (red line #5 machine-enforced) ───────────────────
def test_quote_over_15_words_fails_lint(tmp_path):
    long_q = " ".join(["w"] * 16)
    rel = REL_OK + f"\n    quote: {long_q}"
    errs = lint_dir(setup(tmp_path, page(rel)))
    assert any("quote" in e and "15" in e for e in errs)

def test_quote_within_15_words_passes(tmp_path):
    rel = REL_OK + "\n    quote: We purchase memory from SK Hynix Micron and Samsung"
    errs = lint_dir(setup(tmp_path, page(rel)))
    assert not any("quote" in e for e in errs)
