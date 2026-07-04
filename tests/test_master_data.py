from warehouse import reference

def test_47_afro_countries():
    df = reference.countries()
    assert len(df) == 47
    assert df["iso3"].nunique() == 47
    assert (df["who_region"] == "AFRO").all()

def test_indicator_catalogue_domains():
    cat = reference.indicator_catalogue()
    for d in ("hiv", "maternal", "uhc", "tb", "malaria"):
        assert d in set(cat["domain"])

def test_iso3_lookup():
    assert reference.iso3_of("Kenya") == "KEN"
    assert reference.iso3_of("Nowhere") is None
