"""Unit tests for agent-facing tools."""

import pytest
from unittest.mock import patch, MagicMock
from tools import search_flights, compare_price, AGENT_TOOLS_SCHEMA, TOOL_DISPATCHER
from models import FlightOption, FareResult


def test_exactly_two_agent_facing_tools():
    """Verify that exactly two tools are exposed to the agent."""
    assert len(AGENT_TOOLS_SCHEMA) == 2
    tool_names = [t["function"]["name"] for t in AGENT_TOOLS_SCHEMA]
    assert "search_flights" in tool_names
    assert "compare_price" in tool_names

    # Check dispatcher contains only these two
    assert set(TOOL_DISPATCHER.keys()) == {"search_flights", "compare_price"}


def test_search_flights_tool_resolution_and_call():
    mock_flight = FlightOption(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    with patch("tools.aviationstack_client.search_flights", return_value=[mock_flight]):
        res = search_flights("Delhi", "Mumbai", "2026-09-24")
        assert res["status"] == "success"
        assert res["origin"] == "DEL"
        assert res["destination"] == "BOM"
        assert len(res["flights"]) == 1
        assert res["flights"][0]["flight_number"] == "6E327"


def test_search_flights_unresolvable_city():
    res = search_flights("UnknownCityXYZ999", "Mumbai", "2026-09-24")
    assert res["status"] == "error"
    assert "Could not resolve origin airport" in res["message"]


def test_compare_price_tool():
    options = [
        {
            "flight_number": "6E327",
            "airline": "IndiGo",
            "airline_code": "6E",
            "origin": "DEL",
            "destination": "BOM",
            "travel_date": "2026-09-24",
            "departure_time": "08:10",
            "arrival_time": "10:20",
            "stops": 0,
            "source": "AviationStack",
        }
    ]
    mock_fare = FareResult(
        flight_number="6E327",
        airline="IndiGo",
        airline_code="6E",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        currency="INR",
        price_available=True,
        price_status="verified",
        ignav_id="ignav_test_123",
        stops=0
    )
    with patch("tools.ignav_client.search_one_way_fares", return_value=[mock_fare]):
        res = compare_price(options)
        assert res["status"] == "success"
        assert len(res["fares"]) == 1
        matched_fare = res["fares"][0]
        assert matched_fare["flight_number"] == "6E327"
        assert matched_fare["price"] == 6247.0
        assert matched_fare["price_status"] == "verified"
        assert matched_fare["ignav_id"] == "ignav_test_123"
