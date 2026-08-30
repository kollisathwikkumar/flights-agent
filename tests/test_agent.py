"""Unit tests for Agent Orchestration and decision workflow."""

import pytest
from unittest.mock import patch, MagicMock
from agent import FlightOptionFinderAgent
from memory import SessionMemory
from models import FlightOption, FareResult, BookingOption, ScrapingVerificationResult


@pytest.fixture
def agent_instance():
    mem = SessionMemory()
    return FlightOptionFinderAgent(memory=mem)


def test_agent_query_parsing(agent_instance):
    query = "Find me a flight from Delhi to Mumbai on September 24 under ₹8,000"
    req = agent_instance.parse_user_query(query)
    assert req.origin_city == "Delhi"
    assert req.destination_city == "Mumbai"
    assert req.travel_date == "2026-09-24"
    assert req.budget == 8000.0


def test_agent_budget_rejection(agent_instance):
    """Test that flights exceeding budget are rejected."""
    expensive_fare = FareResult(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=9500.0,  # Exceeds ₹8000
        currency="INR",
        price_available=True,
        price_status="verified",
        ignav_id="ignav_exp_1",
    )
    with patch("agent.search_flights", return_value={"status": "success", "flights": []}):
        with patch("agent.ignav_client.search_one_way_fares", return_value=[expensive_fare]):
            res = agent_instance.run("Find me a flight from Delhi to Mumbai on September 24 under ₹8,000")
            assert res.best_flight is None
            assert "Price:\nUNAVAILABLE" in res.formatted_response


def test_agent_successful_selection(agent_instance):
    """Test full decision pipeline with a valid within-budget flight."""
    valid_fare = FareResult(
        flight_number="6E327",
        airline="IndiGo",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        departure_time="08:10",
        arrival_time="10:20",
        price=6247.0,
        currency="INR",
        price_available=True,
        price_status="verified",
        ignav_id="ignav_test_123",
    )
    mock_booking = BookingOption(
        provider="IndiGo",
        provider_type="airline",
        price=6247.0,
        currency="INR",
        url="https://www.goindigo.in/booking/sample",
    )
    mock_ver = ScrapingVerificationResult(
        status="passed",
        url="https://www.goindigo.in/booking/sample",
        extracted_flight_number="6E327",
        extracted_fare=6247.0,
        details="Verified",
    )

    with patch("agent.search_flights", return_value={"status": "success", "flights": []}):
        with patch("agent.ignav_client.search_one_way_fares", return_value=[valid_fare]):
            with patch("agent.ignav_client.get_booking_links", return_value=[mock_booking]):
                with patch("agent.booking_verifier.verify_booking_page", return_value=mock_ver):
                    res = agent_instance.run("Find me a flight from Delhi to Mumbai on September 24 under ₹8,000")
                    assert res.best_flight is not None
                    assert res.best_flight.flight_number == "6E327"
                    assert res.best_flight.price == 6247.0
                    assert res.best_flight.price_status == "verified"
                    assert res.best_flight.booking_provider == "IndiGo"
                    assert res.best_flight.web_verification_status == "passed"
                    assert "✈️ BEST FLIGHT" in res.formatted_response
                    assert "₹6,247 INR" in res.formatted_response
                    assert "PASSED" in res.formatted_response


def test_agent_trace_completeness(agent_instance):
    """Ensure trace records PLAN, ACT, OBSERVE, EVALUATE, DECIDE."""
    valid_fare = FareResult(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
        price=6247.0,
        price_available=True,
        price_status="verified",
    )
    with patch("agent.search_flights", return_value={"status": "success", "flights": []}):
        with patch("agent.ignav_client.search_one_way_fares", return_value=[valid_fare]):
            res = agent_instance.run("Delhi to Mumbai on September 24 under ₹8,000")
            phases = [step.phase for step in res.trace]
            assert "PLAN" in phases
            assert "ACT" in phases
            assert "OBSERVE" in phases
            assert "EVALUATE" in phases
            assert "DECIDE" in phases
