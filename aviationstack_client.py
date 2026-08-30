"""AviationStack API client for real flight schedules and status.

Communicates with AviationStack endpoint:
- GET /v1/flights

Handles plan capability limits, normalizes to FlightOption, and maintains strict data provenance.
"""

import time
import logging
from typing import Any, Optional
from datetime import datetime, timezone
import requests

from config import config
from models import FlightOption

logger = logging.getLogger(__name__)


class AviationStackError(Exception):
    """Base exception for AviationStack API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class AviationStackFutureDateUnavailableError(AviationStackError):
    """Raised when the configured AviationStack subscription plan cannot retrieve future dates."""
    pass


class AviationStackClient:
    """Client for AviationStack Flights API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else config.aviationstack_api_key
        self.base_url = (base_url or config.aviationstack_base_url).rstrip("/")

    def _format_time(self, scheduled_str: Optional[str]) -> Optional[str]:
        """Extract HH:MM from ISO timestamp."""
        if not scheduled_str:
            return None
        raw = str(scheduled_str).strip()
        if "T" in raw:
            time_part = raw.split("T")[-1]
            return time_part[:5]
        if len(raw) >= 5 and ":" in raw:
            return raw[:5]
        return raw

    def search_flights(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        limit: int = 100,
    ) -> list[FlightOption]:
        """Search flight schedules for an origin, destination, and travel date.
        
        If the account's subscription plan cannot access the requested future date,
        raises AviationStackFutureDateUnavailableError or returns a controlled state without fabricating data.
        """
        if not self.api_key:
            raise AviationStackError("AVIATIONSTACK_API_KEY is not configured.")

        origin = origin.strip().upper()
        destination = destination.strip().upper()
        travel_date = travel_date.strip()

        # Check if the requested date is today in UTC
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        is_today = travel_date == today_utc

        url = f"{self.base_url}/flights"
        params: dict[str, Any] = {
            "access_key": self.api_key,
            "dep_iata": origin,
            "arr_iata": destination,
            "limit": limit,
        }

        # If requesting a future date, attempting to pass flight_date may fail on free plans
        # Attempt with flight_date first to verify plan capabilities
        if not is_today:
            params["flight_date"] = travel_date

        max_attempts = 2
        last_err: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, params=params, timeout=20)
                
                # Check for API-level error payloads (AviationStack returns HTTP 200 or 403 with error JSON)
                try:
                    data = response.json()
                except ValueError:
                    data = None

                if isinstance(data, dict) and "error" in data:
                    err_obj = data["error"]
                    err_code = str(err_obj.get("code", ""))
                    err_msg = str(err_obj.get("message", err_obj))

                    if err_code == "function_access_restricted" or "subscription plan" in err_msg:
                        raise AviationStackFutureDateUnavailableError(
                            f"AviationStack future-date capability unavailable for the configured plan/account: {err_msg}",
                            status_code=response.status_code,
                            error_code=err_code,
                        )
                    if err_code in ("missing_access_key", "invalid_access_key", "inactive_user"):
                        raise AviationStackError(
                            f"AviationStack authentication error: {err_msg}",
                            status_code=response.status_code,
                            error_code=err_code,
                        )
                    raise AviationStackError(
                        f"AviationStack error ({err_code}): {err_msg}",
                        status_code=response.status_code,
                        error_code=err_code,
                    )

                if not response.ok:
                    raise AviationStackError(
                        f"AviationStack HTTP error {response.status_code}: {response.text[:300]}",
                        status_code=response.status_code,
                    )

                if not data or not isinstance(data, dict):
                    return []

                raw_flights = data.get("data") or []
                return self._parse_flights(raw_flights, origin, destination, travel_date)

            except (requests.Timeout, requests.ConnectionError) as e:
                last_err = e
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise AviationStackError(f"Network error connecting to AviationStack: {str(e)}") from e

        if last_err:
            raise AviationStackError(f"AviationStack request failed: {str(last_err)}")
        return []

    def _parse_flights(
        self,
        raw_flights: list[dict[str, Any]],
        origin: str,
        destination: str,
        travel_date: str,
    ) -> list[FlightOption]:
        """Normalize raw AviationStack flight items into FlightOption models."""
        options: list[FlightOption] = []

        for item in raw_flights:
            if not isinstance(item, dict):
                continue

            flight_date = item.get("flight_date") or travel_date
            
            # Enforce hard date constraint: if the record does not match the requested travel_date, do not include it
            if str(flight_date) != str(travel_date):
                continue

            airline_info = item.get("airline") or {}
            flight_info = item.get("flight") or {}
            dep_info = item.get("departure") or {}
            arr_info = item.get("arrival") or {}

            flight_iata = flight_info.get("iata")
            airline_iata = airline_info.get("iata")
            flight_number_raw = flight_info.get("number")
            airline_name = airline_info.get("name")

            if flight_iata:
                flight_number = str(flight_iata).replace(" ", "").upper()
            elif airline_iata and flight_number_raw:
                flight_number = f"{airline_iata}{flight_number_raw}".replace(" ", "").upper()
            elif flight_number_raw:
                flight_number = str(flight_number_raw).replace(" ", "").upper()
            else:
                continue

            dep_iata = dep_info.get("iata") or origin
            arr_iata = arr_info.get("iata") or destination

            dep_time = self._format_time(dep_info.get("scheduled") or dep_info.get("estimated"))
            arr_time = self._format_time(arr_info.get("scheduled") or arr_info.get("estimated"))

            options.append(
                FlightOption(
                    flight_number=flight_number,
                    airline=airline_name,
                    airline_code=airline_iata,
                    origin=str(dep_iata).upper(),
                    destination=str(arr_iata).upper(),
                    travel_date=str(flight_date),
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    departure_timezone=dep_info.get("timezone"),
                    arrival_timezone=arr_info.get("timezone"),
                    stops=0,
                    source="AviationStack",
                )
            )

        return options


# Singleton
aviationstack_client = AviationStackClient()
