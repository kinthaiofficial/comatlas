"""Entity resolution: surface form -> canonical id (consensus votes compare AFTER this)."""
import re
from scripts.ontology import load_alias_map

_SUFFIX = re.compile(
    r"[\s,]+(inc\.?|corp\.?|corporation|co\.?(,)?(\s+ltd\.?)?|ltd\.?|limited|plc|company|holdings?)\.?$",
    re.IGNORECASE)


def slugify(surface: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", surface.strip().lower()).strip("-")


def _candidates(surface: str):
    s = surface.strip()
    yield s
    prev = None
    while prev != s:                      # strip stacked suffixes ("Co., Ltd.")
        prev, s = s, _SUFFIX.sub("", s).strip().rstrip(",")
        yield s


def normalize_surface(surface: str, alias_map: dict | None = None) -> tuple[str, bool]:
    amap = alias_map if alias_map is not None else load_alias_map()
    cands = list(_candidates(surface))
    for cand in cands:
        cid = amap.get(cand.casefold())
        if cid is not None:
            return cid, True
    return slugify(cands[-1]), False
