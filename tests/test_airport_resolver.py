"""Unit tests for airport resolver."""

import pytest
from airport_resolver import resolve_airport


def test_resolve_standard_cities():
    del_res = resolve_airport("Delhi")
    assert del_res is not None
    assert del_res.code == "DEL"
    assert del_res.city == "Delhi"

    bom_res = resolve_airport("Mumbai")
    assert bom_res is not None
    assert bom_res.code == "BOM"

    blr_res = resolve_airport("Bangalore")
    assert blr_res is not None
    assert blr_res.code == "BLR"

    blr_res2 = resolve_airport("Bengaluru")
    assert blr_res2 is not None
    assert blr_res2.code == "BLR"


def test_resolve_direct_iata_codes():
    res = resolve_airport("DEL")
    assert res is not None
    assert res.code == "DEL"

    res_lower = resolve_airport("bom")
    assert res_lower is not None
    assert res_lower.code == "BOM"


def test_resolve_aliases():
    res1 = resolve_airport("Bombay")
    assert res1 is not None
    assert res1.code == "BOM"

    res2 = resolve_airport("New Delhi")
    assert res2 is not None
    assert res2.code == "DEL"

    res3 = resolve_airport("Calcutta")
    assert res3 is not None
    assert res3.code == "CCU"


def test_resolve_ambiguous_city():
    res = resolve_airport("Goa", prefer_primary_for_ambiguous=False)
    assert res is not None
    assert res.is_ambiguous is True
    assert "GOI" in res.possible_codes
    assert "GOX" in res.possible_codes


def test_resolve_unknown():
    res = resolve_airport("AtlantisNonExistentCity12345")
    assert res is None
