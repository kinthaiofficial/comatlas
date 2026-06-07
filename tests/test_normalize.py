from scripts.normalize import normalize_surface, slugify

AMAP = {"nvidia": "nvidia", "nvda": "nvidia", "taiwan semiconductor": "tsmc", "tsmc": "tsmc"}

def test_known_alias_resolves():
    assert normalize_surface("NVDA", AMAP) == ("nvidia", True)
    assert normalize_surface("Taiwan Semiconductor", AMAP) == ("tsmc", True)

def test_corporate_suffix_stripped_before_lookup():
    assert normalize_surface("NVIDIA Corporation", AMAP) == ("nvidia", True)
    assert normalize_surface("Taiwan Semiconductor Co., Ltd.", AMAP) == ("tsmc", True)

def test_unknown_surface_slugified_not_known():
    cid, known = normalize_surface("Foxconn Industrial Internet", AMAP)
    assert (cid, known) == ("foxconn-industrial-internet", False)

def test_slugify():
    assert slugify("SK hynix Inc.") == "sk-hynix-inc"
