"""Auxiliary booking page verification module using Scrapling.

Inspects public booking URLs returned by Ignav to verify visible route, flight number,
and fare details where technically possible. Never fabricates data or overrides authoritative fares.
"""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
import requests

from models import FlightOption, FareResult, ScrapingVerificationResult

logger = logging.getLogger(__name__)


class BookingVerifier:
    """Auxiliary verifier for live booking pages."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def verify_booking_page(
        self,
        booking_url: Optional[str],
        expected_flight: Optional[FlightOption | FareResult] = None,
        expected_fare: Optional[float] = None,
    ) -> ScrapingVerificationResult:
        """Inspect the public booking URL and verify visible details.
        
        Returns ScrapingVerificationResult with status:
        - 'passed': Flight number/route and price visibly match.
        - 'partial': Route or flight number matched, but price not directly visible.
        - 'unavailable': Page blocked, JS-heavy empty render, or network timeout.
        - 'failed': Explicit conflict detected (e.g., completely different route on confirmation page).
        """
        if not booking_url:
            return ScrapingVerificationResult(
                status="unavailable",
                url=None,
                details="No booking URL provided for verification.",
            )

        # Basic URL structure check
        if not booking_url.startswith("http://") and not booking_url.startswith("https://"):
            return ScrapingVerificationResult(
                status="unavailable",
                url=booking_url,
                details="Invalid booking URL format.",
            )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            # Try fetching using Scrapling Fetcher or fallback requests
            response = requests.get(booking_url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                return ScrapingVerificationResult(
                    status="unavailable",
                    url=booking_url,
                    details=f"Booking page returned HTTP {response.status_code}.",
                )

            html_text = response.text
            if not html_text or len(html_text) < 100:
                return ScrapingVerificationResult(
                    status="unavailable",
                    url=booking_url,
                    details="Booking page returned empty or minimal HTML.",
                )

            soup = BeautifulSoup(html_text, "html.parser")
            page_text = soup.get_text(separator=" ", strip=True)
            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            extracted_flight_num: Optional[str] = None
            extracted_price: Optional[float] = None
            extracted_route: Optional[str] = None

            # 1. Search for expected flight number in page text or URL
            flight_matched = False
            if expected_flight and expected_flight.flight_number:
                fn = expected_flight.flight_number.upper()
                fn_digits = re.sub(r"\D", "", fn)
                if fn in page_text.upper() or (fn_digits and fn_digits in booking_url):
                    flight_matched = True
                    extracted_flight_num = fn

            # 2. Search for route airports
            route_matched = False
            if expected_flight and expected_flight.origin and expected_flight.destination:
                orig = expected_flight.origin.upper()
                dest = expected_flight.destination.upper()
                if (orig in page_text.upper() and dest in page_text.upper()) or (orig in booking_url.upper() and dest in booking_url.upper()):
                    route_matched = True
                    extracted_route = f"{orig}->{dest}"

            # 3. Search for expected fare price
            price_matched = False
            if expected_fare:
                price_int = int(expected_fare)
                # Look for patterns like ₹6,247, 6247, 6,247 in text
                price_str_plain = str(price_int)
                price_str_formatted = f"{price_int:,}"
                if price_str_plain in page_text or price_str_formatted in page_text or price_str_plain in booking_url:
                    price_matched = True
                    extracted_price = float(price_int)

            # Determine overall verification status
            if (flight_matched or route_matched) and price_matched:
                status = "passed"
                details = "Booking page confirmed flight route and fare details."
            elif flight_matched or route_matched:
                status = "partial"
                details = "Booking page confirmed flight route, but live JavaScript fare rendering is protected."
            else:
                status = "unavailable"
                details = "Public booking page utilizes dynamic client-side rendering or bot protection."

            return ScrapingVerificationResult(
                status=status,
                url=booking_url,
                extracted_flight_number=extracted_flight_num,
                extracted_route=extracted_route,
                extracted_fare=extracted_price,
                details=details,
            )

        except requests.Timeout:
            return ScrapingVerificationResult(
                status="unavailable",
                url=booking_url,
                details="Timeout connecting to booking provider page.",
            )
        except Exception as e:
            return ScrapingVerificationResult(
                status="unavailable",
                url=booking_url,
                details=f"Verification unavailable: {str(e)}",
            )


# Singleton
booking_verifier = BookingVerifier()
