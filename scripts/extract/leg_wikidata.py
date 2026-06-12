"""Deterministic leg: Wikidata SPARQL for corporate structure (curated; trusted, no voting).

Emits structured edges (from_structured, extractor='wikidata') for the filer's subsidiaries and
equity stakes. `to_edges` is pure (fixture-tested); `extract` runs the live SPARQL query."""
import json, os, urllib.parse, urllib.request

ENDPOINT = os.environ.get("WIKIDATA_ENDPOINT", "https://query.wikidata.org/sparql")
SOURCE_ID = "wikidata-q182477"
SOURCE_URL = "https://www.wikidata.org/wiki/Q182477"

# Wikidata property -> (predicate, orientation). The filer is NVIDIA (Q182477).
#   P355  has subsidiary : filer P355 X   => X SUBSIDIARY_OF filer
#   P1830 owner of       : filer P1830 X  => filer OWNS_STAKE_IN X
PROPS = {"P355": ("SUBSIDIARY_OF", "incoming"), "P1830": ("OWNS_STAKE_IN", "outgoing")}

QUERY = """SELECT ?prop ?other ?label WHERE {
  VALUES ?prop { wdt:P355 wdt:P1830 }
  wd:%s ?prop ?other .
  ?other rdfs:label ?label . FILTER(LANG(?label) = "en")
}"""


def to_edges(bindings: list[dict], filer_label: str, as_of: str) -> list[dict]:
    """SPARQL JSON bindings -> normalized-input edge dicts (surfaces; pipeline normalizes/guards)."""
    edges = []
    for b in bindings:
        prop = b["prop"]["value"].rsplit("/", 1)[-1]          # ".../P355" -> "P355"
        spec = PROPS.get(prop)
        if not spec:
            continue
        predicate, orientation = spec
        other = b["label"]["value"]
        subj, obj = (other, filer_label) if orientation == "incoming" else (filer_label, other)
        edges.append({"subject": subj, "subject_type": "Company", "object": obj, "object_type": "Company",
                      "predicate": predicate, "as_of": as_of, "evidence": f"Wikidata {prop}: {other}",
                      "source": SOURCE_ID, "extractor": "wikidata", "from_structured": True})
    return edges


def extract(filer_qid: str = "Q182477", filer_label: str = "NVIDIA", as_of: str = "2026-Q1") -> list[dict]:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": QUERY % filer_qid, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "ComAtlas/1.0 (research)",
                                               "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return to_edges(data["results"]["bindings"], filer_label, as_of)
