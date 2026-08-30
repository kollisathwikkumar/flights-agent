"""Unit tests for AviationStack API client parsing and error handling."""

import pytest
from unittest.mock import patch, MagicMock
from aviationstack_client import AviationStackClient, AviationStackError, AviationStackFutureDateUnavailableError
from models import FlightOption


@pytest.fixture
def client():
    return AviationStackClient(api_key="test_aviation_key", base_url="http://api.aviationstack.com/v1")


def test_aviationstack_parse_flights(client):
    mock_data = [
        {
            "flight_date": "2026-08-30",
            "flight_status": "scheduled",
            "departure": {
                "airport": "Indira Gandhi International",
                "timezone": "Asia/Kolkata",
                "iata": "DEL",
                "scheduled": "2026-08-30T18:00:00+00:00"
            },
            "arrival": {
                "airport": "Chhatrapati Shivaji International",
                "timezone": "Asia/Kolkata",
                "iata": "BOM",
                "scheduled": "2026-08-30T20:15:00+00:00"
            },
            "airline": {
                "name": "IndiGo",
                "iata": "6E"
            },
            "flight": {
                "number": "329",
                "iata": "6E329"
            }
        }
    ]
    flights = client._parse_flights(mock_data, origin="DEL", destination="BOM", travel_date="2026-08-30")
    assert len(flights) == 1
    f = flights[0]
    assert f.flight_number == "6E329"
    assert f.airline == "IndiGo"
    assert f.airline_code == "6E"
    assert f.origin == "DEL"
    assert f.destination == "BOM"
    assert f.travel_date == "2026-08-30"
    assert f.departure_time == "18:00"
    assert f.arrival_time == "20:15"
    assert f.source == "AviationStack"


def test_aviationstack_future_date_restricted_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {
        "error": {
            "code": "function_access_restricted",
            "message": "Your current subscription plan does not support this API function."
        }
    }
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(AviationStackFutureDateUnavailableError, match="future-date capability unavailable"):
            client.search_flights("DEL", "BOM", "2026-09-24")


def test_aviationstack_date_filter_rejection(client):
    """Ensure flights with dates other than requested date are filtered out."""
    mock_data = [
        {
            "flight_date": "2026-08-29",
            "departure": {"iata": "DEL", "scheduled": "2026-08-29T10:00:00"},
            "arrival": {"iata": "BOM", "scheduled": "2026-08-29T12:00:00"},
            "airline": {"name": "IndiGo", "iata": "6E"},
            "flight": {"iata": "6E101"}
        }
    ]
    flights = client._parse_flights(mock_data, origin="DEL", destination="BOM", travel_date="2026-08-30")
    assert len(flights) == 0


def test_aviationstack_missing_key():
    client_no_key = AviationStackClient(api_key="")
    with pytest.raises(AviationStackError, match="AVIATIONSTACK_API_KEY is not configured"):
        client_no_key.search_flights("DEL", "BOM", "2026-08-30")
