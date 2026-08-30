"""Unit tests for Scrapling booking page verification."""

import pytest
from unittest.mock import patch, MagicMock
from scraping.booking_verifier import BookingVerifier
from models import FlightOption, FareResult


@pytest.fixture
def verifier():
    return BookingVerifier(timeout=5)


def test_scraping_no_url(verifier):
    res = verifier.verify_booking_page(None)
    assert res.status == "unavailable"
    assert res.url is None


def test_scraping_passed_verification(verifier):
    mock_html = """
    <html>
        <head><title>IndiGo Booking Confirmation</title></head>
        <body>
            <h1>Flight 6E327 - Delhi to Mumbai</h1>
            <p>Route: DEL to BOM</p>
            <p>Total Fare: ₹6,247 INR</p>
        </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html

    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    with patch("requests.get", return_value=mock_resp):
        res = verifier.verify_booking_page(
            booking_url="https://www.goindigo.in/booking/sample",
            expected_flight=flight,
            expected_fare=6247.0
        )
        assert res.status == "passed"
        assert res.extracted_flight_number == "6E327"
        assert res.extracted_fare == 6247.0


def test_scraping_partial_verification(verifier):
    mock_html = """
    <html>
        <head><title>IndiGo Flight Select</title></head>
        <body>
            <h1>Select flights from DEL to BOM</h1>
            <div>Loading live dynamic seat map...</div>
        </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html

    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    with patch("requests.get", return_value=mock_resp):
        res = verifier.verify_booking_page(
            booking_url="https://www.goindigo.in/booking/sample",
            expected_flight=flight,
            expected_fare=6247.0
        )
        assert res.status == "partial"


def test_scraping_unavailable_on_timeout(verifier):
    flight = FlightOption(
        flight_number="6E327",
        origin="DEL",
        destination="BOM",
        travel_date="2026-09-24",
    )
    with patch("requests.get", side_effect=Exception("Connection timed out")):
        res = verifier.verify_booking_page(
            booking_url="https://www.airline.com/booking",
            expected_flight=flight,
            expected_fare=6247.0
        )
        assert res.status == "unavailable"
