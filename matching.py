"""Deterministic Matching Engine for Flight Schedules and Fares.

Compares AviationStack FlightOption records with Ignav FareResult records
under strict deterministic rules without LLM intervention.
"""

import re
import logging
from typing import Optional
from models import FlightOption, FareResult

logger = logging.getLogger(__name__)


def normalize_flight_number(raw: Optional[str]) -> str:
    """Normalize flight number into standard uppercase alphanumeric format (e.g. '6E-327' -> '6E327')."""
    if not raw:
        return ""
    # Strip spaces, dashes, slashes, dots
    cleaned = re.sub(r"[\s\-\/\.]", "", str(raw)).strip().upper()
    return cleaned


def extract_carrier_and_number(normalized: str) -> tuple[str, str]:
    """Extract 2-character carrier code and numeric flight number if present."""
    match = re.match(r"^([A-Z0-9]{2})(\d+)$", normalized)
    if match:
        return match.group(1), match.group(2)
    return "", normalized


def is_exact_flight_match(flight: FlightOption, fare: FareResult) -> bool:
    """Deterministic check if an AviationStack flight and an Ignav fare record represent the exact same flight."""
    # 1. Hard constraint: Route Match (Origin & Destination)
    if flight.origin.upper() != fare.origin.upper():
        return False
    if flight.destination.upper() != fare.destination.upper():
        return False

    # 2. Hard constraint: Travel Date Match
    if flight.travel_date != fare.travel_date:
        return False

    # 3. Flight Number Normalization & Comparison
    flight_norm = normalize_flight_number(flight.flight_number)
    fare_norm = normalize_flight_number(fare.flight_number)

    if not flight_norm or not fare_norm:
        return False

    f_carrier, f_num = extract_carrier_and_number(flight_norm)
    fare_carrier, fare_num = extract_carrier_and_number(fare_norm)

    if flight_norm != fare_norm:
        # Check if numbers match and carriers match via code or airline code
        if f_num and fare_num and f_num == fare_num:
            # Check carrier codes
            c1 = f_carrier or (flight.airline_code.upper() if flight.airline_code else "")
            c2 = fare_carrier or (fare.airline_code.upper() if fare.airline_code else "")
            if c1 and c2 and c1 != c2:
                return False
        else:
            return False

    # 4. Airline Name Check (if both provided, avoid conflicting airlines)
    if flight.airline and fare.airline:
        a1 = flight.airline.strip().lower()
        a2 = fare.airline.strip().lower()
        # Direct equality or containment (e.g. 'IndiGo' vs 'IndiGo Airlines')
        if a1 != a2 and a1 not in a2 and a2 not in a1:
            return False

    # 5. Nonstop vs Segment constraint
    if flight.stops != fare.stops:
        # Single nonstop flight segment must not match a multi-stop itinerary
        return False

    # 6. Departure time validation (if both available)
    if flight.departure_time and fare.departure_time:
        # Compare HH:MM
        t1 = flight.departure_time[:5]
        t2 = fare.departure_time[:5]
        if t1 != t2:
            # Allow at most 15-minute schedule difference due to timezone/padding if present, but for exact match prefer exact
            t1_parts = t1.split(":")
            t2_parts = t2.split(":")
            if len(t1_parts) == 2 and len(t2_parts) == 2:
                try:
                    m1 = int(t1_parts[0]) * 60 + int(t1_parts[1])
                    m2 = int(t2_parts[0]) * 60 + int(t2_parts[1])
                    if abs(m1 - m2) > 30:
                        return False
                except ValueError:
                    pass

    return True


def match_flights_with_fares(
    flights: list[FlightOption],
    fares: list[FareResult],
) -> list[FareResult]:
    """Deterministically match a list of flights with a list of fares.
    
    For each flight:
      - If an exact matching fare exists in `fares`, populate fare details and preserve status.
      - If no exact matching fare exists, produce an unmatched FareResult with price_status='unavailable'.
    """
    matched_results: list[FareResult] = []

    for flight in flights:
        matched_fare: Optional[FareResult] = None
        for fare in fares:
            if is_exact_flight_match(flight, fare):
                matched_fare = fare
                break

        if matched_fare is not None:
            # Preserve fare status directly from Ignav
            matched_results.append(
                FareResult(
                    flight_number=flight.flight_number,
                    airline=flight.airline or matched_fare.airline,
                    airline_code=flight.airline_code or matched_fare.airline_code,
                    origin=flight.origin,
                    destination=flight.destination,
                    travel_date=flight.travel_date,
                    departure_time=flight.departure_time or matched_fare.departure_time,
                    arrival_time=flight.arrival_time or matched_fare.arrival_time,
                    price=matched_fare.price,
                    currency=matched_fare.currency or "INR",
                    price_available=matched_fare.price is not None,
                    price_status=matched_fare.price_status,
                    ignav_id=matched_fare.ignav_id,
                    booking_url=matched_fare.booking_url,
                    booking_provider=matched_fare.booking_provider,
                    booking_provider_type=matched_fare.booking_provider_type,
                    source="Ignav",
                    web_verification_status="unavailable",
                    stops=flight.stops,
                )
            )
        else:
            # No matching fare
            matched_results.append(
                FareResult(
                    flight_number=flight.flight_number,
                    airline=flight.airline,
                    airline_code=flight.airline_code,
                    origin=flight.origin,
                    destination=flight.destination,
                    travel_date=flight.travel_date,
                    departure_time=flight.departure_time,
                    arrival_time=flight.arrival_time,
                    price=None,
                    currency=None,
                    price_available=False,
                    price_status="unavailable",
                    ignav_id=None,
                    booking_url=None,
                    booking_provider=None,
                    booking_provider_type=None,
                    source="Ignav",
                    web_verification_status="unavailable",
                    stops=flight.stops,
                )
            )

    return matched_results
