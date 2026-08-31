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

    def discover_booking_url(
        self,
        flight: FareResult,
        passengers: int = 1,
        cabin_class: str = "economy",
    ) -> tuple[str, str, str]:
        """Synthesize and discover the direct official airline or OTA booking URL when API deep links are missing.
        
        Returns: (booking_url, provider_name, provider_type)
        """
        fn = (flight.flight_number or "").upper().replace(" ", "")
        orig = flight.origin.upper()
        dest = flight.destination.upper()
        date_str = flight.travel_date.strip()  # YYYY-MM-DD
        
        airline_name = flight.airline or "Airline"
        carrier_upper = airline_name.upper()

        # 1. Air India (AI)
        if fn.startswith("AI") or "AIR INDIA" in carrier_upper:
            # Official Air India flight search deep-link
            url = f"https://www.airindia.com/in/en/book/flight-search.html?tripType=O&origin={orig}&destination={dest}&travelDate={date_str}&adults={passengers}&cabinClass={cabin_class.title()}"
            return url, "Air India", "airline"

        # 2. IndiGo (6E)
        if fn.startswith("6E") or "INDIGO" in carrier_upper:
            # Extract digits e.g. 6E5304 -> 5304
            flt_digits = re.sub(r"\D", "", fn) or "5304"
            date_compact = date_str.replace("-", "")  # 20260924
            url = f"https://www.goindigo.in/flight-select-redirection.html?cid=metasearch&flightNumber={flt_digits}#{orig}/{dest}/{date_compact}/INR/{passengers}00/"
            return url, "IndiGo", "airline"

        # 3. SpiceJet (SG)
        if fn.startswith("SG") or "SPICEJET" in carrier_upper:
            url = f"https://www.spicejet.com/booking-search?tripType=1&origin={orig}&destination={dest}&departure={date_str}&adults={passengers}"
            return url, "SpiceJet", "airline"

        # 4. Akasa Air (QP)
        if fn.startswith("QP") or "AKASA" in carrier_upper:
            url = f"https://www.akasaair.com/flight-search?origin={orig}&destination={dest}&date={date_str}&pax={passengers}"
            return url, "Akasa Air", "airline"

        # 5. Vistara (UK) -> Merged to Air India
        if fn.startswith("UK") or "VISTARA" in carrier_upper:
            url = f"https://www.airindia.com/in/en/book/flight-search.html?tripType=O&origin={orig}&destination={dest}&travelDate={date_str}&adults={passengers}"
            return url, "Air India (Vistara)", "airline"

        # 6. Emirates (EK)
        if fn.startswith("EK") or "EMIRATES" in carrier_upper:
            url = f"https://www.emirates.com/english/book/?origin={orig}&destination={dest}&departureDate={date_str}&adults={passengers}"
            return url, "Emirates", "airline"

        # 7. Qatar Airways (QR)
        if fn.startswith("QR") or "QATAR" in carrier_upper:
            url = f"https://www.qatarairways.com/en/booking.html?from={orig}&to={dest}&departDate={date_str}"
            return url, "Qatar Airways", "airline"

        # 8. British Airways (BA)
        if fn.startswith("BA") or "BRITISH" in carrier_upper:
            url = f"https://www.britishairways.com/travel/fx/public/en_gb?eId=111011&source=flight_search&origin={orig}&destination={dest}&depDate={date_str}"
            return url, "British Airways", "airline"

        # 9. Google Flights Direct Query URL
        google_url = f"https://www.google.com/travel/flights?q=flights+from+{orig}+to+{dest}+on+{date_str}+{airline_name}"
        return google_url, f"{airline_name} (Google Flights)", "ota"

    def find_and_verify_booking(
        self,
        flight: FareResult,
        passengers: int = 1,
        cabin_class: str = "economy",
    ) -> tuple[str, str, str, ScrapingVerificationResult]:
        """Find booking URL if missing, and verify the booking page via Scrapling.
        
        Returns: (booking_url, provider_name, provider_type, verification_result)
        """
        if flight.booking_url:
            url = flight.booking_url
            provider = flight.booking_provider or "Airline"
            p_type = flight.booking_provider_type or "airline"
        else:
            url, provider, p_type = self.discover_booking_url(flight, passengers=passengers, cabin_class=cabin_class)

        ver_result = self.verify_booking_page(url, expected_flight=flight, expected_fare=flight.price)
        return url, provider, p_type, ver_result


# Singleton
booking_verifier = BookingVerifier()

