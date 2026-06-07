"""Unit tests for the heuristic bill parser (pure, no PDF library)."""
from app.services import bill_parser as b


def test_number_eu_us_formats():
    assert b.parse_number("1.234,56") == 1234.56     # EU
    assert b.parse_number("1,234.56") == 1234.56     # US
    assert b.parse_number("1.234") == 1234.0         # EU thousands
    assert b.parse_number("1234.5") == 1234.5        # decimal
    assert b.parse_number("1,5") == 1.5              # EU decimal
    assert b.parse_number("12.50") == 12.5
    assert b.parse_number("3.456.789") == 3456789.0
    assert b.parse_number("— kWh") is None
    assert b.parse_number(None) is None


def test_period_en_de_tr():
    assert b.normalize_period("2024-03") == "2024-03"
    assert b.normalize_period("03/2024") == "2024-03"
    assert b.normalize_period("March 2024") == "2024-03"
    assert b.normalize_period("März 2024") == "2024-03"   # DE
    assert b.normalize_period("Mart 2024") == "2024-03"   # TR
    assert b.normalize_period("Aralık 2023") == "2023-12"  # TR December
    assert b.normalize_period("nothing here") is None


def test_table_en_headers():
    t = [["Month", "Consumption (kWh)", "Cost (EUR)"],
         ["2024-01", "1.234,5", "250,40"],
         ["2024-02", "1.100", "230,00"]]
    r = b.parse_bill(tables=[t])
    assert r["source"] == "table" and len(r["rows"]) == 2
    assert r["rows"][0] == {"period": "2024-01", "energy_kwh": 1234.5, "cost_eur": 250.4}
    assert r["rows"][1]["energy_kwh"] == 1100.0


def test_table_de_headers():
    t = [["Monat", "Verbrauch", "Betrag"], ["Januar 2024", "980", "210,5"]]
    r = b.parse_bill(tables=[t])
    assert len(r["rows"]) == 1
    assert r["rows"][0] == {"period": "2024-01", "energy_kwh": 980.0, "cost_eur": 210.5}


def test_text_fallback_de():
    txt = "Stromrechnung\nMärz 2024  1.234 kWh  250,50 €\nApril 2024 1.100 kWh 230,00 EUR\n"
    r = b.parse_bill(text=txt)
    assert r["source"] == "text" and len(r["rows"]) == 2
    assert r["rows"][0] == {"period": "2024-03", "energy_kwh": 1234.0, "cost_eur": 250.5}


def test_dedup_and_sort():
    t = [["period", "kwh"], ["2024-02", "100"], ["2024-01", "200"], ["2024-02", "999"]]
    r = b.parse_bill(tables=[t])
    assert [x["period"] for x in r["rows"]] == ["2024-01", "2024-02"]
    assert r["rows"][1]["energy_kwh"] == 100.0   # first 2024-02 wins


def test_empty_warns():
    r = b.parse_bill(text="no consumption data")
    assert r["rows"] == [] and r["source"] == "none"
    assert "No monthly" in r["warnings"][0]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
