"""Loaders for the closed-set ontology. The YML files are human-owned."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load_entity_types() -> set[str]:
    data = yaml.safe_load((ROOT / "ontology" / "entity_types.yml").read_text())
    return set(data["entity_types"])

def load_predicates() -> dict:
    data = yaml.safe_load((ROOT / "ontology" / "predicates.yml").read_text())
    return data["predicates"]

def load_alias_map() -> dict[str, str]:
    """Invert alias_map.yml to {surface.casefold(): canonical_id}."""
    data = yaml.safe_load((ROOT / "ontology" / "alias_map.yml").read_text())
    inv: dict[str, str] = {}
    for cid, aliases in data.items():
        inv[cid.casefold()] = cid
        for a in aliases or []:
            inv[str(a).casefold()] = cid
    return inv


def edge_satisfies_ontology(edge: dict, predicates: dict | None = None) -> tuple[bool, str]:
    """Return (True, '') if subject_type ∈ domain and target_type ∈ range for the predicate.

    Returns (False, reason) when the edge violates the ontology's domain/range constraints.
    edge dict must have keys: predicate, subject_type, target_type.
    predicates defaults to load_predicates() when not supplied.
    """
    if predicates is None:
        predicates = load_predicates()
    pred = edge.get("predicate", "")
    spec = predicates.get(pred)
    if spec is None:
        return False, f"predicate '{pred}' not in closed set"
    subj_type = edge.get("subject_type", "")
    tgt_type = edge.get("target_type", "")
    if subj_type not in spec["domain"]:
        return False, f"subject type {subj_type} not in domain({pred}) {spec['domain']}"
    if tgt_type not in spec["range"]:
        return False, f"target type {tgt_type} not in range({pred}) {spec['range']}"
    return True, ""
