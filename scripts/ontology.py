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
