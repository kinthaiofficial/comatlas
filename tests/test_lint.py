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
