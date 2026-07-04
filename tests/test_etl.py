from etl import get_client
from etl.clients import WorldBankClient

def test_worldbank_url_and_parse():
    c = get_client("worldbank")
    url = c.build_url("NY.GDP.PCAP.CD", iso3="KEN", start=2015, end=2020)
    assert "NY.GDP.PCAP.CD" in url and "KEN" in url
    payload = [{"pages": 1}, [
        {"countryiso3code": "KEN", "date": "2019", "value": 1800.0,
         "indicator": {"id": "NY.GDP.PCAP.CD"}}]]
    rows = c.parse(payload)
    assert rows[0]["iso3"] == "KEN" and rows[0]["year"] == 2019

def test_validate_drops_null_values():
    c = WorldBankClient()
    clean = c.validate([{"value": 1}, {"value": None}, {"value": 3}])
    assert len(clean) == 2
