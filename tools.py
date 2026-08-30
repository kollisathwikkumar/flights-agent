"""Agent tools module for T10 Flight Option Finder.

Exposes EXACTLY TWO agent-facing tools to NVIDIA NIM:
1. search_flights: Retrieves real flight schedules using AviationStack.
2. compare_price: Retrieves real fares from Ignav and deterministically matches them.

All other components (Ignav client, AviationStack client, Airport Resolver,
Matching Engine, Booking Links, Scrapling) are internal.
"""

import logging
from typing import Any, Union
from models import FlightOption, FareResult
from airport_resolver import resolve_airport
from aviationstack_client import aviationstack_client, AviationStackFutureDateUnavailableError
from ignav_client import ignav_client
from matching import match_flights_with_fares

logger = logging.getLogger(__name__)


def search_flights(
    origin: str,
    destination: str,
    travel_date: str,
    passengers: int = 1,
    cabin_class: str = "economy",
) -> dict[str, Any]:
    """Search for real flight schedules between origin and destination on a specific date.
    
    Args:
        origin: City name or 3-letter IATA code of origin (e.g. 'Delhi' or 'DEL').
        destination: City name or 3-letter IATA code of destination (e.g. 'Mumbai' or 'BOM').
        travel_date: Travel date in YYYY-MM-DD format (e.g. '2026-09-24').
        passengers: Number of passengers (default: 1).
        cabin_class: Cabin class (default: 'economy').
        
    Returns:
        A dictionary containing resolved route details, status, and list of FlightOption records.
    """
    # 1. Resolve airports internally
    orig_res = resolve_airport(origin)
    dest_res = resolve_airport(destination)

    if not orig_res:
        return {
            "status": "error",
            "message": f"Could not resolve origin airport for '{origin}'. Please clarify the origin city.",
            "flights": [],
        }
    if not dest_res:
        return {
            "status": "error",
            "message": f"Could not resolve destination airport for '{destination}'. Please clarify the destination city.",
            "flights": [],
        }

    origin_code = orig_res.code
    destination_code = dest_res.code

    # 2. Query AviationStack for real flight schedules
    try:
        flights = aviationstack_client.search_flights(
            origin=origin_code,
            destination=destination_code,
            travel_date=travel_date,
        )
        return {
            "status": "success",
            "origin": origin_code,
            "origin_city": orig_res.city,
            "destination": destination_code,
            "destination_city": dest_res.city,
            "travel_date": travel_date,
            "count": len(flights),
            "flights": [f.model_dump() for f in flights],
        }
    except AviationStackFutureDateUnavailableError as e:
        return {
            "status": "future_date_unavailable",
            "message": str(e),
            "origin": origin_code,
            "origin_city": orig_res.city,
            "destination": destination_code,
            "destination_city": dest_res.city,
            "travel_date": travel_date,
            "count": 0,
            "flights": [],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving flights from AviationStack: {str(e)}",
            "origin": origin_code,
            "origin_city": orig_res.city,
            "destination": destination_code,
            "destination_city": dest_res.city,
            "travel_date": travel_date,
            "count": 0,
            "flights": [],
        }


def compare_price(options: Union[list[dict], list[FlightOption]]) -> dict[str, Any]:
    """Retrieve authoritative fares from Ignav and deterministically match them with the provided flight options.
    
    Args:
        options: A list of FlightOption dictionaries or objects (typically returned by search_flights).
        
    Returns:
        A dictionary containing matched fares with exact prices and verification statuses.
    """
    if not options:
        return {
            "status": "error",
            "message": "No flight options provided for price comparison.",
            "fares": [],
        }

    # Normalize input into FlightOption instances
    flight_options: list[FlightOption] = []
    for opt in options:
        if isinstance(opt, FlightOption):
            flight_options.append(opt)
        elif isinstance(opt, dict):
            try:
                flight_options.append(FlightOption(**opt))
            except Exception:
                continue

    if not flight_options:
        return {
            "status": "error",
            "message": "Invalid flight option format provided.",
            "fares": [],
        }

    # Derive route and travel date from the flight options
    first_opt = flight_options[0]
    origin = first_opt.origin
    destination = first_opt.destination
    travel_date = first_opt.travel_date

    # 1. Perform ONE route/date fare search via Ignav
    try:
        raw_fares = ignav_client.search_one_way_fares(
            origin=origin,
            destination=destination,
            departure_date=travel_date,
        )
    except Exception as e:
        logger.error(f"Ignav fare search failed: {e}")
        # When Ignav fails, return unmatched results with unavailable status
        unmatched = [
            FareResult(
                flight_number=f.flight_number,
                airline=f.airline,
                airline_code=f.airline_code,
                origin=f.origin,
                destination=f.destination,
                travel_date=f.travel_date,
                departure_time=f.departure_time,
                arrival_time=f.arrival_time,
                price=None,
                price_available=False,
                price_status="unavailable",
            )
            for f in flight_options
        ]
        return {
            "status": "error",
            "message": f"Ignav fare search failed: {str(e)}",
            "count": len(unmatched),
            "fares": [f.model_dump() for f in unmatched],
        }

    # 2. Deterministic local matching
    matched_results = match_flights_with_fares(flight_options, raw_fares)

    return {
        "status": "success",
        "origin": origin,
        "destination": destination,
        "travel_date": travel_date,
        "count": len(matched_results),
        "fares": [f.model_dump() for f in matched_results],
    }


# Tool Definitions for OpenAI / NVIDIA NIM Function Calling
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for real flight schedules between origin and destination on a given travel date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin city name or 3-letter IATA code (e.g. 'Delhi' or 'DEL')."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination city name or 3-letter IATA code (e.g. 'Mumbai' or 'BOM')."
                    },
                    "travel_date": {
                        "type": "string",
                        "description": "Travel date in YYYY-MM-DD format (e.g. '2026-09-24')."
                    },
                    "passengers": {
                        "type": "integer",
                        "description": "Number of passengers (default 1)."
                    },
                    "cabin_class": {
                        "type": "string",
                        "description": "Cabin class e.g. 'economy', 'premium_economy', 'business', 'first'."
                    }
                },
                "required": ["origin", "destination", "travel_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_price",
            "description": "Retrieve live fares and match prices against flight schedule options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "options": {
                        "type": "array",
                        "description": "List of flight schedule option objects returned by search_flights.",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["options"]
            }
        }
    }
]

TOOL_DISPATCHER = {
    "search_flights": search_flights,
    "compare_price": compare_price,
}
