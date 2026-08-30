"""Ignav API client for real flight fares and booking links.

Communicates with Ignav endpoints:
- POST /api/fares/one-way
- POST /api/fares/booking-links

Maintains strict provenance, preserves verified/unverified status, and handles errors cleanly.
"""

import time
import logging
from typing import Any, Optional, Literal
import requests

from config import config
from models import FareResult, BookingOption

logger = logging.getLogger(__name__)


class IgnavError(Exception):
    """Base exception for Ignav API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class IgnavClient:
    """Client for Ignav Flight Fares and Booking Links API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else config.ignav_api_key
        self.base_url = (base_url or config.ignav_base_url).rstrip("/")

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise IgnavError("IGNAV_API_KEY is not configured.")
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, json_data: Optional[dict] = None) -> dict[str, Any]:
        """Execute an HTTP request to Ignav with 1 transient retry."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        max_attempts = 2
        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=20,
                )

                if response.status_code in (401, 403):
                    raise IgnavError(
                        f"Ignav authentication/authorization failed (HTTP {response.status_code}). Check your IGNAV_API_KEY.",
                        status_code=response.status_code,
                        response_body=response.text[:500],
                    )

                if response.status_code == 400:
                    raise IgnavError(
                        f"Ignav bad request (HTTP 400): {response.text[:500]}",
                        status_code=400,
                        response_body=response.text[:500],
                    )

                if response.status_code == 429:
                    raise IgnavError(
                        "Ignav rate limit exceeded (HTTP 429).",
                        status_code=429,
                        response_body=response.text[:500],
                    )

                if response.status_code >= 500:
                    if attempt < max_attempts:
                        time.sleep(1.0)
                        continue
                    raise IgnavError(
                        f"Ignav server error (HTTP {response.status_code}).",
                        status_code=response.status_code,
                        response_body=response.text[:500],
                    )

                if not response.ok:
                    raise IgnavError(
                        f"Ignav request failed with status {response.status_code}: {response.text[:500]}",
                        status_code=response.status_code,
                        response_body=response.text[:500],
                    )

                try:
                    return response.json()
                except ValueError as e:
                    raise IgnavError("Ignav returned invalid JSON response.", response_body=response.text[:500]) from e

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise IgnavError(f"Network error connecting to Ignav: {str(e)}") from e

        if last_error:
            raise IgnavError(f"Ignav request failed after retries: {str(last_error)}")
        raise IgnavError("Ignav request failed unexpectedly.")

    def search_one_way_fares(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        cabin_class: str = "economy",
        market: str = "IN",
        max_stops: Optional[int] = None,
        preferred_airline: Optional[str] = None,
    ) -> list[FareResult]:
        """Search one-way fares using POST /api/fares/one-way."""
        payload: dict[str, Any] = {
            "origin": origin.strip().upper(),
            "destination": destination.strip().upper(),
            "departure_date": departure_date.strip(),
            "adults": int(adults),
            "cabin_class": cabin_class.strip().lower(),
            "market": market.strip().upper(),
        }
        if max_stops is not None:
            payload["max_stops"] = int(max_stops)
        if preferred_airline:
            payload["preferred_airline"] = preferred_airline.strip()

        data = self._make_request("POST", "fares/one-way", json_data=payload)
        return self._parse_fares_response(data, origin=origin, destination=destination, travel_date=departure_date)

    def _format_time(self, raw_time: Optional[str]) -> Optional[str]:
        """Format ISO timestamp or time string into HH:MM format."""
        if not raw_time:
            return None
        raw = str(raw_time).strip()
        if "T" in raw:
            time_part = raw.split("T")[-1]
            return time_part[:5]
        if len(raw) >= 5 and ":" in raw:
            return raw[:5]
        return raw

    def _parse_fares_response(
        self,
        data: dict[str, Any],
        origin: str,
        destination: str,
        travel_date: str,
    ) -> list[FareResult]:
        """Defensively parse Ignav fare response into FareResult objects."""
        results: list[FareResult] = []
        if not isinstance(data, dict):
            return results

        itineraries = data.get("itineraries") or data.get("data") or data.get("results") or []
        if isinstance(data, list):
            itineraries = data

        for item in itineraries:
            if not isinstance(item, dict):
                continue

            ignav_id = item.get("ignav_id") or item.get("id")

            # Extract price details
            price_val: Optional[float] = None
            currency_val: Optional[str] = "INR"
            status_val: str = "unverified"

            raw_price = item.get("price")
            if isinstance(raw_price, dict):
                amount = raw_price.get("amount") or raw_price.get("total") or raw_price.get("value")
                if amount is not None:
                    try:
                        price_val = float(amount)
                    except (ValueError, TypeError):
                        price_val = None
                currency_val = raw_price.get("currency") or "INR"
                raw_status = (raw_price.get("status") or "").lower().strip()
                if raw_status == "verified":
                    status_val = "verified"
                elif raw_status == "unverified":
                    status_val = "unverified"
                elif raw_status:
                    status_val = raw_status
            elif raw_price is not None:
                try:
                    price_val = float(raw_price)
                except (ValueError, TypeError):
                    price_val = None
                status_val = item.get("status", "unverified").lower()
                currency_val = item.get("currency", "INR")

            # Extract flight & segment details
            outbound = item.get("outbound") or {}
            segments = outbound.get("segments") or item.get("segments") or []

            airline_name = item.get("carrier") or outbound.get("carrier") or item.get("airline")
            airline_code: Optional[str] = None
            flight_number_val: Optional[str] = None
            dep_time: Optional[str] = None
            arr_time: Optional[str] = None
            dep_airport = origin
            arr_airport = destination
            stops_count = len(segments) - 1 if len(segments) > 0 else 0

            if segments and isinstance(segments, list):
                first_seg = segments[0] if isinstance(segments[0], dict) else {}
                last_seg = segments[-1] if isinstance(segments[-1], dict) else {}

                airline_code = (
                    first_seg.get("marketing_carrier_code")
                    or first_seg.get("carrier_code")
                    or first_seg.get("carrier")
                )
                flight_num_only = (
                    first_seg.get("flight_number")
                    or first_seg.get("marketing_flight_number")
                    or first_seg.get("number")
                )
                if flight_num_only:
                    flight_num_str = str(flight_num_only).strip()
                    if airline_code and not flight_num_str.upper().startswith(str(airline_code).upper()):
                        flight_number_val = f"{airline_code}{flight_num_str}"
                    else:
                        flight_number_val = flight_num_str

                if not airline_name:
                    airline_name = first_seg.get("operating_carrier_name") or first_seg.get("carrier_name") or first_seg.get("airline")

                dep_airport = first_seg.get("departure_airport") or first_seg.get("origin") or dep_airport
                arr_airport = last_seg.get("arrival_airport") or last_seg.get("destination") or arr_airport

                dep_time = self._format_time(first_seg.get("departure_time_local") or first_seg.get("departure_time"))
                arr_time = self._format_time(last_seg.get("arrival_time_local") or last_seg.get("arrival_time"))

            if not flight_number_val:
                flight_number_val = item.get("flight_number") or outbound.get("flight_number")

            if not flight_number_val:
                continue

            final_status: Literal["verified", "unverified", "unavailable", "error"] = "unverified"
            if status_val == "verified":
                final_status = "verified"
            elif status_val == "unavailable":
                final_status = "unavailable"
            elif status_val == "error":
                final_status = "error"
            else:
                final_status = "unverified"

            results.append(
                FareResult(
                    flight_number=str(flight_number_val).replace(" ", "").upper(),
                    airline=str(airline_name) if airline_name else None,
                    airline_code=str(airline_code).upper() if airline_code else None,
                    origin=str(dep_airport).upper(),
                    destination=str(arr_airport).upper(),
                    travel_date=travel_date,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    price=price_val,
                    currency=str(currency_val).upper() if currency_val else "INR",
                    price_available=price_val is not None,
                    price_status=final_status,
                    ignav_id=str(ignav_id) if ignav_id else None,
                    booking_url=None,
                    booking_provider=None,
                    booking_provider_type=None,
                    source="Ignav",
                    web_verification_status="unavailable",
                    stops=max(0, stops_count),
                )
            )

        return results

    def get_booking_links(self, ignav_id: str) -> list[BookingOption]:
        """Fetch real booking links for a specific ignav_id using POST /api/fares/booking-links."""
        if not ignav_id:
            return []

        payload = {"ignav_id": str(ignav_id).strip()}
        data = self._make_request("POST", "fares/booking-links", json_data=payload)

        options: list[BookingOption] = []
        if not isinstance(data, dict):
            return options

        raw_options = (
            data.get("booking_options")
            or data.get("options")
            or data.get("links")
            or data.get("data")
            or []
        )
        if isinstance(data, list):
            raw_options = data

        for item in raw_options:
            if not isinstance(item, dict):
                continue
            
            # Check if this item has nested 'links'
            links_list = item.get("links")
            if isinstance(links_list, list) and links_list:
                for link_entry in links_list:
                    if not isinstance(link_entry, dict):
                        continue
                    url = link_entry.get("url") or link_entry.get("link")
                    provider = (
                        link_entry.get("provider_name")
                        or link_entry.get("provider")
                        or link_entry.get("name")
                        or "Airline"
                    )
                    provider_type = link_entry.get("provider_type") or link_entry.get("type")
                    if url:
                        options.append(
                            BookingOption(
                                provider=str(provider),
                                provider_type=str(provider_type) if provider_type else None,
                                price=item.get("price"),
                                currency=item.get("currency"),
                                url=str(url),
                            )
                        )
            else:
                url = item.get("url") or item.get("booking_url") or item.get("link")
                provider = item.get("provider") or item.get("provider_name") or item.get("name") or "Airline"
                if url:
                    opt_price: Optional[float] = None
                    if "price" in item and item["price"] is not None:
                        try:
                            opt_price = float(item["price"])
                        except (ValueError, TypeError):
                            opt_price = None

                    options.append(
                        BookingOption(
                            provider=str(provider),
                            provider_type=item.get("provider_type") or item.get("type"),
                            price=opt_price,
                            currency=item.get("currency"),
                            url=str(url),
                        )
                    )

        return options


# Singleton
ignav_client = IgnavClient()
