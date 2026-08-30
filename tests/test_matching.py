"""Unit tests for deterministic matching engine."""

import pytest
from models import FlightOption, FareResult
from matching import (
    normalize_flight_number,
    is_exact_flight_match,
    match_flights_with_fares,
)


def test_normalize_flight_number():
    assert normalize_flight_number("6E327") == "6E327"
    assert normalize_flight_number("6E-327") == "6E327"
    assert normalize_flight_number("6e 327") == "6E327"
    assert normalize_flight_number("6E / 327") == "6E327"
    assert normalize_flight_number("AI 865") == "AI865"


def test_critical_matching_exact_match():
    """Section 43 Critical Test 1: Exact Match."""
    flight = FlightOption(
        flight_number="6E327",
        airline="IndiGo",
        airline_code="6E",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        departure_time="08:10",
        arrival_time="10:20"
    )
    fare = FareResult(
        flight_number="6E327",
        airline="IndiGo",
        airline_code="6E",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        departure_time="08:10",
        arrival_time="10:20",
        price=6247.0,
        currency="INR",
        price_available=True,
        price_status="verified",
        ignav_id="ignav_exact_123"
    )

    assert is_exact_flight_match(flight, fare) is True
    matched = match_flights_with_fares([flight], [fare])
    assert len(matched) == 1
    assert matched[0].price == 6247.0
    assert matched[0].price_status == "verified"
    assert matched[0].ignav_id == "ignav_exact_123"
    assert matched[0].price_available is True


def test_critical_matching_wrong_flight_number():
    """Section 43 Critical Test 2: Wrong Flight Number."""
    flight = FlightOption(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    fare = FareResult(
        flight_number="6E521",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=7100.0,
        price_status="verified"
    )

    assert is_exact_flight_match(flight, fare) is False
    matched = match_flights_with_fares([flight], [fare])
    assert len(matched) == 1
    assert matched[0].price is None
    assert matched[0].price_status == "unavailable"
    assert matched[0].price_available is False


def test_critical_matching_reversed_route():
    """Section 43 Critical Test 3: DEL->BOM vs BOM->DEL."""
    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    fare = FareResult(
        flight_number="6E327",
        origin="BOM",
        destination="DEL",
        travel_date="2026-09-24",
        price=6247.0,
        price_status="verified"
    )
    assert is_exact_flight_match(flight, fare) is False


def test_critical_matching_wrong_date():
    """Section 43 Critical Test 4: 2026-09-24 vs 2026-09-25."""
    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    fare = FareResult(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        price_status="verified"
    )
    # Different date
    fare.travel_date = "2026-09-25"
    assert is_exact_flight_match(flight, fare) is False


def test_matching_wrong_airline():
    flight = FlightOption(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    fare = FareResult(
        flight_number="6E327",
        airline="Air India",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        price_status="verified"
    )
    assert is_exact_flight_match(flight, fare) is False


def test_matching_stops_mismatch():
    """Nonstop flight cannot match 1-stop itinerary."""
    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        stops=0
    )
    fare = FareResult(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        stops=1
    )
    assert is_exact_flight_match(flight, fare) is False


def test_matching_preserves_unverified_status():
    flight = FlightOption(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    fare = FareResult(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        price_status="unverified"
    )
    matched = match_flights_with_fares([flight], [fare])
    assert len(matched) == 1
    assert matched[0].price_status == "unverified"
    assert matched[0].price == 6247.0
