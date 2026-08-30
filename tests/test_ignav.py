"""Unit tests for Ignav API client parsing and error handling."""

import pytest
from unittest.mock import patch, MagicMock
from ignav_client import IgnavClient, IgnavError
from models import FareResult, BookingOption


@pytest.fixture
def client():
    return IgnavClient(api_key="test_ignav_key", base_url="https://test.ignav.com/api")


def test_ignav_parse_verified_fare(client):
    mock_payload = {
        "itineraries": [
            {
                "ignav_id": "ignav_test_1",
                "price": {"amount": 6247.0, "currency": "INR", "status": "verified"},
                "outbound": {
                    "carrier": "IndiGo",
                    "segments": [
                        {
                            "marketing_carrier_code": "6E",
                            "flight_number": "327",
                            "operating_carrier_name": "IndiGo",
                            "departure_airport": "DEL",
                            "arrival_airport": "BOM",
                            "departure_time_local": "2026-09-24T08:10:00",
                            "arrival_time_local": "2026-09-24T10:20:00"
                        }
                    ]
                }
            }
        ]
    }
    fares = client._parse_fares_response(mock_payload, origin="DEL", destination="BOM", travel_date="2026-09-24")
    assert len(fares) == 1
    fare = fares[0]
    assert fare.flight_number == "6E327"
    assert fare.airline == "IndiGo"
    assert fare.airline_code == "6E"
    assert fare.origin == "DEL"
    assert fare.destination == "BOM"
    assert fare.travel_date == "2026-09-24"
    assert fare.departure_time == "08:10"
    assert fare.arrival_time == "10:20"
    assert fare.price == 6247.0
    assert fare.currency == "INR"
    assert fare.price_available is True
    assert fare.price_status == "verified"
    assert fare.ignav_id == "ignav_test_1"
    assert fare.stops == 0


def test_ignav_parse_unverified_fare(client):
    mock_payload = {
        "itineraries": [
            {
                "ignav_id": "ignav_test_unverified",
                "price": {"amount": 7100.0, "currency": "INR", "status": "unverified"},
                "outbound": {
                    "carrier": "Air India",
                    "segments": [
                        {
                            "marketing_carrier_code": "AI",
                            "flight_number": "865",
                            "departure_airport": "DEL",
                            "arrival_airport": "BOM",
                            "departure_time_local": "2026-09-24T10:00:00",
                            "arrival_time_local": "2026-09-24T12:15:00"
                        }
                    ]
                }
            }
        ]
    }
    fares = client._parse_fares_response(mock_payload, origin="DEL", destination="BOM", travel_date="2026-09-24")
    assert len(fares) == 1
    assert fares[0].price_status == "unverified"
    assert fares[0].price == 7100.0


def test_ignav_parse_booking_links(client):
    mock_payload = {
        "booking_options": [
            {
                "legs": ["outbound"],
                "links": [
                    {
                        "provider_name": "IndiGo",
                        "provider_type": "airline",
                        "url": "https://www.goindigo.in/booking/sample"
                    }
                ]
            },
            {
                "provider": "MakeMyTrip",
                "provider_type": "ota",
                "url": "https://www.makemytrip.com/booking/sample",
                "price": 6300.0
            }
        ]
    }
    with patch.object(client, "_make_request", return_value=mock_payload):
        links = client.get_booking_links("ignav_test_1")
        assert len(links) == 2
        assert links[0].provider == "IndiGo"
        assert links[0].provider_type == "airline"
        assert links[0].url == "https://www.goindigo.in/booking/sample"
        assert links[1].provider == "MakeMyTrip"
        assert links[1].provider_type == "ota"


def test_ignav_empty_booking_links(client):
    with patch.object(client, "_make_request", return_value={"booking_options": []}):
        links = client.get_booking_links("ignav_none")
        assert links == []


def test_ignav_auth_error_raises():
    client_no_key = IgnavClient(api_key="")
    with pytest.raises(IgnavError, match="IGNAV_API_KEY is not configured"):
        client_no_key.search_one_way_fares("DEL", "BOM", "2026-09-24")
