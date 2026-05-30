from app.services.polyelectrolytes import load_catalog, CATALOG_IDS


def test_catalog_loads_all_entries():
    entries = load_catalog()
    ids = {e["id"] for e in entries}
    assert {"PEI", "PAH", "PSS", "PDADMAC", "PAA", "Chitosan", "PEG", "MXene"} <= ids


def test_catalog_ids_constant_matches():
    entries = load_catalog()
    assert set(CATALOG_IDS) == {e["id"] for e in entries}


def test_pss_is_strong_anion():
    entries = {e["id"]: e for e in load_catalog()}
    pss = entries["PSS"]
    assert pss["charge_sign"] == -1
    assert pss["is_strong"] is True
    assert pss["pka"] is None
