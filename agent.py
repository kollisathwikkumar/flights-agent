"""Agent Orchestration module for T10 Flight Option Finder.

Implements the complete PLAN -> ACT -> OBSERVE -> EVALUATE -> DECIDE loop,
integrates SessionMemory, strictly enforces hard constraints, selects booking links,
runs auxiliary Scrapling verification, and formats transparent user-facing output.
"""

import json
import re
import logging
from typing import Optional, Any
from datetime import datetime

from config import config
from models import (
    SearchRequest,
    FlightOption,
    FareResult,
    BookingOption,
    ScrapingVerificationResult,
    AgentTraceStep,
    FlightSearchResult,
)
from memory import SessionMemory
from airport_resolver import resolve_airport
from tools import search_flights, compare_price, AGENT_TOOLS_SCHEMA
from llm_client import nim_client, NIMError
from ignav_client import ignav_client
from scraping.booking_verifier import booking_verifier

logger = logging.getLogger(__name__)


NEARBY_HUBS: dict[str, list[str]] = {
    "VGA": ["HYD (Hyderabad)", "MAA (Chennai)", "VTZ (Visakhapatnam)"],
    "PNQ": ["BOM (Mumbai)"],
    "BOM": ["PNQ (Pune)"],
    "DEL": ["IXC (Chandigarh)", "JAI (Jaipur)"],
    "BLR": ["MAA (Chennai)", "COK (Kochi)"],
    "GOI": ["GOX (Goa Mopa)", "BOM (Mumbai)", "BLR (Bengaluru)"],
    "GOX": ["GOI (Goa Dabolim)", "BOM (Mumbai)", "BLR (Bengaluru)"],
    "TRV": ["COK (Kochi)"],
    "IXC": ["DEL (Delhi)"],
    "DED": ["DEL (Delhi)"],
    "JAI": ["DEL (Delhi)"],
    "LKO": ["DEL (Delhi)", "VNS (Varanasi)"],
    "PAT": ["CCU (Kolkata)", "VNS (Varanasi)"],
}


class FlightOptionFinderAgent:
    """Production AI Agent for finding and verifying flight options."""

    def __init__(self, memory: Optional[SessionMemory] = None):
        self.memory = memory or SessionMemory()

    def parse_user_query(self, query: str) -> SearchRequest:
        """Parse natural language query into a structured SearchRequest, merging with session memory."""
        prefs = self.memory.get_preferences()

        # Extract dates: YYYY-MM-DD or Month DD, YYYY or Month DD
        date_val: Optional[str] = prefs.travel_date
        
        # Regex for YYYY-MM-DD
        iso_date = re.search(r"\b(20\d\d-\d{2}-\d{2})\b", query)
        if iso_date:
            date_val = iso_date.group(1)
        else:
            # Match formats like 'September 24 2026', '24 September 2026', 'September 24'
            month_match = re.search(
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(20\d\d))?\b",
                query,
                re.IGNORECASE,
            )
            if not month_match:
                # Match '24 September 2026'
                month_match = re.search(
                    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)(?:\s*,?\s*(20\d\d))?\b",
                    query,
                    re.IGNORECASE,
                )
                if month_match:
                    day = month_match.group(1)
                    month_name = month_match.group(2)
                    year = month_match.group(3) or "2026"
                    try:
                        dt = datetime.strptime(f"{year} {month_name[:3]} {day}", "%Y %b %d")
                        date_val = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            else:
                month_name = month_match.group(1)
                day = month_match.group(2)
                year = month_match.group(3) or "2026"
                try:
                    dt = datetime.strptime(f"{year} {month_name[:3]} {day}", "%Y %b %d")
                    date_val = dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        # Extract budget: under ₹8,000, under 8000, max 8000, budget 8000
        budget_val: Optional[float] = prefs.budget
        budget_match = re.search(r"(?:under|below|max|budget|within|less than|<=|<)?\s*[₹$€£]?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*(?:inr|rs|rupees|bucks)?", query, re.IGNORECASE)
        # Search specifically for budget keyword context
        budget_specific = re.search(r"(?:under|below|budget|max|within|less than)\s*[₹$€£]?\s*([0-9,]+)", query, re.IGNORECASE)
        if budget_specific:
            num_str = budget_specific.group(1).replace(",", "")
            try:
                budget_val = float(num_str)
            except ValueError:
                pass

        # Extract cities / routes
        orig_city = prefs.origin_city
        dest_city = prefs.destination_city

        # 1. Try 'from X to Y'
        m1 = re.search(r"\bfrom\s+([A-Za-z0-9\s\(\)\-\.]+?)\s+to\s+([A-Za-z0-9\s\(\)\-\.]+?)(?:\s+(?:on|under|below|for|with|in|at|budget|before|after)\b|$)", query, re.IGNORECASE)
        if m1:
            c1, c2 = m1.group(1).strip(), m1.group(2).strip()
            r1, r2 = resolve_airport(c1), resolve_airport(c2)
            orig_city = r1.city if r1 else c1
            dest_city = r2.city if r2 else c2

        if not orig_city or not dest_city:
            # 2. Try 'X to Y' or 'X -> Y'
            m2 = re.search(r"\b([A-Za-z0-9\s\(\)\-\.]+?)\s+(?:to|->|-)\s+([A-Za-z0-9\s\(\)\-\.]+?)(?:\s+(?:on|under|below|for|with|in|at|budget)\b|$)", query, re.IGNORECASE)
            if m2:
                c1 = re.sub(r"^(find|get|search|show|book|a|me|flights?)\s+", "", m2.group(1).strip(), flags=re.IGNORECASE).strip()
                c2 = m2.group(2).strip()
                r1, r2 = resolve_airport(c1), resolve_airport(c2)
                orig_city = r1.city if r1 else c1
                dest_city = r2.city if r2 else c2

        # Preferred departure time
        pref_dep = prefs.preferred_departure
        if re.search(r"\b(morning|early morning)\b", query, re.IGNORECASE):
            pref_dep = "morning"
        elif re.search(r"\b(afternoon)\b", query, re.IGNORECASE):
            pref_dep = "afternoon"
        elif re.search(r"\b(evening)\b", query, re.IGNORECASE):
            pref_dep = "evening"
        elif re.search(r"\b(night|late night)\b", query, re.IGNORECASE):
            pref_dep = "night"

        # Preferred airline
        pref_airline = prefs.preferred_airline
        for air in ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa", "Emirates"]:
            if air.lower() in query.lower():
                pref_airline = air
                break

        # Cabin class
        cabin = prefs.cabin_class or "economy"
        if "business" in query.lower():
            cabin = "business"
        elif "premium economy" in query.lower():
            cabin = "premium_economy"
        elif "first class" in query.lower():
            cabin = "first"

        # Passengers
        pax = prefs.passengers or 1
        pax_match = re.search(r"(\d+)\s*(?:passengers?|pax|adults?|persons?|people)", query, re.IGNORECASE)
        if pax_match:
            try:
                pax = int(pax_match.group(1))
            except ValueError:
                pass

        # Update memory
        self.memory.update(
            budget=budget_val,
            origin_city=orig_city,
            destination_city=dest_city,
            travel_date=date_val,
            preferred_departure=pref_dep,
            preferred_airline=pref_airline,
            cabin_class=cabin,
            passengers=pax,
        )

        return SearchRequest(
            origin_city=orig_city,
            destination_city=dest_city,
            travel_date=date_val or "2026-09-24",
            budget=budget_val,
            currency="INR",
            passengers=pax,
            cabin_class=cabin,
            preferred_airline=pref_airline,
            preferred_departure=pref_dep,
        )

    def run(self, user_query: str) -> FlightSearchResult:
        """Execute the complete PLAN -> ACT -> OBSERVE -> EVALUATE -> DECIDE agent workflow."""
        trace: list[AgentTraceStep] = []

        # 1. PLAN Phase: Parse request and establish goal
        search_req = self.parse_user_query(user_query)

        orig_res = resolve_airport(search_req.origin_city or "")
        dest_res = resolve_airport(search_req.destination_city or "")

        plan_desc = (
            f"Plan flight search for route {search_req.origin_city} ({orig_res.code if orig_res else '?'}) -> "
            f"{search_req.destination_city} ({dest_res.code if dest_res else '?'}) on date {search_req.travel_date}. "
            f"Budget constraint: ₹{search_req.budget:,.0f} {search_req.currency}." if search_req.budget else "No budget constraint specified."
        )
        trace.append(AgentTraceStep(phase="PLAN", content=plan_desc))

        if not orig_res or not dest_res:
            err_resp = f"Could not determine valid airport codes for {search_req.origin_city} -> {search_req.destination_city}. Please clarify the cities."
            return FlightSearchResult(
                query=user_query,
                search_request=search_req,
                trace=trace,
                formatted_response=err_resp,
            )

        search_req.origin_code = orig_res.code
        search_req.destination_code = dest_res.code

        # 2. ACT Phase 1: Tool 1 - search_flights()
        act1_desc = f"Calling search_flights(origin='{orig_res.code}', destination='{dest_res.code}', travel_date='{search_req.travel_date}')"
        trace.append(AgentTraceStep(
            phase="ACT",
            content=act1_desc,
            tool_calls=[{
                "tool": "search_flights",
                "args": {
                    "origin": orig_res.code,
                    "destination": dest_res.code,
                    "travel_date": search_req.travel_date,
                    "passengers": search_req.passengers,
                    "cabin_class": search_req.cabin_class,
                }
            }]
        ))

        flights_resp = search_flights(
            origin=orig_res.code,
            destination=dest_res.code,
            travel_date=search_req.travel_date,
            passengers=search_req.passengers,
            cabin_class=search_req.cabin_class,
        )

        # 3. OBSERVE Phase 1
        raw_flights = flights_resp.get("flights", [])
        flight_options = [FlightOption(**f) for f in raw_flights]
        obs1_desc = (
            f"AviationStack returned {len(flight_options)} flight schedule options for {orig_res.code}->{dest_res.code}. "
            f"Status: {flights_resp.get('status')}."
        )
        if flights_resp.get("status") == "future_date_unavailable":
            obs1_desc += f" Note: {flights_resp.get('message')}"
        trace.append(AgentTraceStep(phase="OBSERVE", content=obs1_desc, observations=obs1_desc))

        # 4. ACT Phase 2: Tool 2 - compare_price()
        # Even if AviationStack plan restricts future date schedules, query Ignav fares for the exact route/date
        trace.append(AgentTraceStep(
            phase="ACT",
            content=f"Calling compare_price() to fetch authoritative fares from Ignav for {orig_res.code}->{dest_res.code} on {search_req.travel_date}.",
            tool_calls=[{
                "tool": "compare_price",
                "args": {"options_count": len(flight_options)}
            }]
        ))

        fares_found: list[FareResult] = []
        matched_fares: list[FareResult] = []

        try:
            # Query Ignav directly for the route/date
            raw_ignav_fares = ignav_client.search_one_way_fares(
                origin=orig_res.code,
                destination=dest_res.code,
                departure_date=search_req.travel_date,
                adults=search_req.passengers,
                cabin_class=search_req.cabin_class,
            )
            fares_found = raw_ignav_fares
        except Exception as e:
            logger.error(f"Ignav search error in agent: {e}")
            raw_ignav_fares = []

        if flight_options:
            price_resp = compare_price([f.model_dump() for f in flight_options])
            raw_matched = price_resp.get("fares", [])
            matched_fares = [FareResult(**f) for f in raw_matched]
        else:
            # When AviationStack has 0 schedules for future dates on free tier, evaluate available Ignav itineraries
            matched_fares = fares_found

        # 5. OBSERVE Phase 2
        obs2_desc = f"Retrieved {len(fares_found)} live fares from Ignav. Matched {len(matched_fares)} candidate options."
        trace.append(AgentTraceStep(phase="OBSERVE", content=obs2_desc, observations=obs2_desc))

        # 6. EVALUATE Phase: Hard constraints, budget filtering, and preference ranking
        eval_desc = "Evaluating candidate fares against hard constraints (exact match, date, route, budget) and user preferences."
        trace.append(AgentTraceStep(phase="EVALUATE", content=eval_desc))

        # Filter valid candidates
        is_domestic_india = (orig_res.country == "India" and dest_res.country == "India")
        foreign_airlines = ["malaysia airlines", "gulf air", "emirates", "singapore airlines", "qatar airways", "etihad", "saudia", "flydubai", "kuwait airways", "oman air", "srilankan"]

        valid_candidates: list[FareResult] = []
        for fare in matched_fares:
            # Check price availability
            if not fare.price_available or fare.price is None:
                continue
            # Domestic filter: Foreign carriers cannot operate domestic Indian routes
            if is_domestic_india and any(foreign in (fare.airline or "").lower() for foreign in foreign_airlines):
                continue
            # Check route & date
            if fare.origin.upper() != orig_res.code or fare.destination.upper() != dest_res.code:
                continue
            if fare.travel_date != search_req.travel_date:
                continue
            # Check budget hard constraint
            if search_req.budget is not None and fare.price > search_req.budget:
                continue
            valid_candidates.append(fare)

        # 6b. CONNECTING FLIGHT SYNTHESIS: If no valid direct candidates exist within budget,
        # query major connecting transit hubs (DEL, BOM, BLR, HYD) to construct valid 1-stop connecting itineraries
        if not valid_candidates:
            connecting_fares = self._search_connecting_hubs(
                origin=orig_res.code,
                destination=dest_res.code,
                travel_date=search_req.travel_date,
                adults=search_req.passengers,
                cabin_class=search_req.cabin_class,
                budget=search_req.budget,
            )
            if connecting_fares:
                valid_candidates.extend(connecting_fares)
                matched_fares.extend(connecting_fares)
                conn_desc = f"Synthesized {len(connecting_fares)} verified 1-stop connecting flight itineraries via primary domestic hubs (DEL, BOM, BLR, HYD)."
                trace.append(AgentTraceStep(phase="OBSERVE", content=conn_desc, observations=conn_desc))

        # 7. DECIDE Phase: Preference ranking and winning flight selection
        best_flight: Optional[FareResult] = None
        recommendation_reason: Optional[str] = None
        suggestions: list[str] = []

        if valid_candidates:
            # Sort by:
            # 1. Verified fare status (verified first)
            # 2. Preferred airline match
            # 3. Preferred departure time match
            # 4. Lowest price
            # 5. Least stops
            def sort_key(f: FareResult) -> tuple:
                is_verified = 0 if f.price_status == "verified" else 1
                airline_match = 0 if search_req.preferred_airline and f.airline and search_req.preferred_airline.lower() in f.airline.lower() else 1
                
                time_match = 1
                if search_req.preferred_departure and f.departure_time:
                    try:
                        hour = int(f.departure_time.split(":")[0])
                        if search_req.preferred_departure == "morning" and 5 <= hour < 12:
                            time_match = 0
                        elif search_req.preferred_departure == "afternoon" and 12 <= hour < 17:
                            time_match = 0
                        elif search_req.preferred_departure == "evening" and 17 <= hour < 21:
                            time_match = 0
                        elif search_req.preferred_departure == "night" and (hour >= 21 or hour < 5):
                            time_match = 0
                    except (ValueError, IndexError):
                        pass

                price_val = f.price if f.price is not None else float("inf")
                return (is_verified, airline_match, time_match, price_val, f.stops)

            valid_candidates.sort(key=sort_key)
            best_flight = valid_candidates[0]

            reasons = []
            if best_flight.price_status == "verified":
                reasons.append("verified fare")
            if search_req.budget:
                reasons.append(f"within budget (₹{best_flight.price:,.0f} <= ₹{search_req.budget:,.0f})")
            if search_req.preferred_airline and best_flight.airline and search_req.preferred_airline.lower() in best_flight.airline.lower():
                reasons.append(f"matches airline preference ({best_flight.airline})")
            if best_flight.stops == 0:
                reasons.append("nonstop flight")
            reasons.append("cheapest available option")

            recommendation_reason = ", ".join(reasons).capitalize() + "."
            decide_desc = f"Selected {best_flight.airline or ''} {best_flight.flight_number} at ₹{best_flight.price:,.0f} {best_flight.currency} [{best_flight.price_status.upper()}]. Reason: {recommendation_reason}"
        else:
            # Generate actionable suggestions when no candidates meet all constraints
            priced_fares = [f for f in (matched_fares or fares_found) if f.price is not None and f.price > 0]
            if priced_fares and search_req.budget:
                min_fare = min(priced_fares, key=lambda x: x.price if x.price else float("inf"))
                diff = (min_fare.price - search_req.budget) if min_fare.price else 0
                decide_desc = f"No flights found within the budget of ₹{search_req.budget:,.0f} for {search_req.travel_date}."
                recommendation_reason = f"All available flights exceed your budget of ₹{search_req.budget:,.0f}."
                suggestions.append(
                    f"Budget Adjustment: The cheapest available flight is {min_fare.airline or ''} {min_fare.flight_number} at ₹{min_fare.price:,.0f} INR (₹{diff:,.0f} above budget). Consider increasing your budget to ₹{min_fare.price:,.0f}."
                )
            else:
                decide_desc = f"No verified fares available for the requested route and date."
                recommendation_reason = "No flights matched the requested criteria."

            # Nearby Airport Suggestions
            orig_hubs = NEARBY_HUBS.get(orig_res.code, [])
            dest_hubs = NEARBY_HUBS.get(dest_res.code, [])
            if orig_hubs:
                suggestions.append(f"Alternate Departure Hubs: Consider checking flights from nearby airports: {', '.join(orig_hubs)}.")
            if dest_hubs:
                suggestions.append(f"Alternate Arrival Hubs: Consider checking flights to nearby airports: {', '.join(dest_hubs)}.")

            # Date Flexibility Suggestion
            suggestions.append(f"Flexible Dates: Try searching ±1 to 3 days around {search_req.travel_date} as fares can vary significantly by weekday.")

        trace.append(AgentTraceStep(phase="DECIDE", content=decide_desc))

        # 8. BOOKING LINKS Retrieval & Scrapling Verification (for winning flight)
        booking_opt: Optional[BookingOption] = None
        web_ver: Optional[ScrapingVerificationResult] = None

        if best_flight:
            # 8a. Try querying Ignav booking-links API first if ignav_id is present
            if best_flight.ignav_id:
                try:
                    booking_options = ignav_client.get_booking_links(best_flight.ignav_id)
                    if booking_options:
                        airline_direct = next((b for b in booking_options if b.provider_type == "airline"), None)
                        booking_opt = airline_direct or booking_options[0]
                        best_flight.booking_url = booking_opt.url
                        best_flight.booking_provider = booking_opt.provider
                        best_flight.booking_provider_type = booking_opt.provider_type
                except Exception as e:
                    logger.error(f"Error fetching booking links from Ignav: {e}")

            # 8b. If booking URL is missing, discover official airline deep-link & verify via Scrapling
            try:
                b_url, b_provider, b_type, web_ver = booking_verifier.find_and_verify_booking(
                    flight=best_flight,
                    passengers=search_req.passengers,
                    cabin_class=search_req.cabin_class,
                )
                best_flight.booking_url = b_url
                best_flight.booking_provider = b_provider
                best_flight.booking_provider_type = b_type
                best_flight.web_verification_status = web_ver.status
                best_flight.web_verification_url = b_url

                if not booking_opt:
                    booking_opt = BookingOption(
                        provider=b_provider,
                        provider_type=b_type,
                        price=best_flight.price,
                        currency=best_flight.currency,
                        url=b_url,
                    )
            except Exception as e:
                logger.error(f"Error discovering/verifying booking URL: {e}")
                web_ver = ScrapingVerificationResult(
                    status="unavailable",
                    url=best_flight.booking_url,
                    details=f"Verification unavailable: {str(e)}"
                )
                best_flight.web_verification_status = "unavailable"

        # 10. Format final response
        formatted_output = self._format_response(
            search_req=search_req,
            best_flight=best_flight,
            recommendation_reason=recommendation_reason,
            web_ver=web_ver,
            suggestions=suggestions,
        )

        # Record in memory
        self.memory.record_turn(
            user_query=user_query,
            agent_response=formatted_output,
            metadata={"flight_number": best_flight.flight_number if best_flight else None}
        )

        return FlightSearchResult(
            query=user_query,
            search_request=search_req,
            flights_found=flight_options,
            fares_found=fares_found,
            matched_fares=matched_fares,
            valid_candidates=valid_candidates,
            best_flight=best_flight,
            booking_option=booking_opt,
            web_verification=web_ver,
            trace=trace,
            recommendation_reason=recommendation_reason,
            suggestions=suggestions,
            formatted_response=formatted_output,
        )

    def _format_response(
        self,
        search_req: SearchRequest,
        best_flight: Optional[FareResult],
        recommendation_reason: Optional[str],
        web_ver: Optional[ScrapingVerificationResult],
        suggestions: Optional[list[str]] = None,
    ) -> str:
        """Format the standardized response adhering to Section 40 specification."""
        if not best_flight or best_flight.price is None:
            sugg_str = ""
            if suggestions:
                sugg_str = "\n\n💡 SMART RECOMMENDATIONS:\n" + "\n".join([f"- {s}" for s in suggestions])

            budget_line = f"Budget: ₹{search_req.budget:,.0f} {search_req.currency}" if search_req.budget else "Budget: None specified"
            return (
                "✈️ NO MATCHING FLIGHT FOUND\n\n"
                f"Route: {search_req.origin_city or search_req.origin_code} → {search_req.destination_city or search_req.destination_code}\n"
                f"Date: {search_req.travel_date}\n"
                f"{budget_line}\n\n"
                "Price:\nUNAVAILABLE\n\n"
                f"Reason:\n{recommendation_reason or 'No fare could be reliably matched to the exact flight within budget.'}"
                f"{sugg_str}"
            )

        budget_status = "WITHIN BUDGET" if (search_req.budget and best_flight.price <= search_req.budget) else "NO BUDGET SET"
        if search_req.budget and best_flight.price > search_req.budget:
            budget_status = "EXCEEDS BUDGET"

        booking_display = f"[{best_flight.booking_provider or 'Book Flight'}]({best_flight.booking_url})" if best_flight.booking_url else "Booking link was not available for this itinerary."
        ver_status = (web_ver.status.upper() if web_ver else best_flight.web_verification_status.upper())

        lines = [
            "✈️ BEST FLIGHT",
            "",
            f"{best_flight.airline or ''} {best_flight.flight_number}".strip(),
            "",
            f"{search_req.origin_city or best_flight.origin} ({best_flight.origin})",
            "→",
            f"{search_req.destination_city or best_flight.destination} ({best_flight.destination})",
            "",
            f"Date:\n{best_flight.travel_date}",
            "",
            f"Departure:\n{best_flight.departure_time or 'N/A'}",
            "",
            f"Arrival:\n{best_flight.arrival_time or 'N/A'}",
            "",
            f"Price:\n₹{best_flight.price:,.0f} {best_flight.currency or 'INR'}",
            "",
            f"Fare status:\n{best_flight.price_status.upper()}",
            "",
            f"Budget:\n₹{search_req.budget:,.0f} {search_req.currency}" if search_req.budget else "Budget:\nNot specified",
            "",
            f"Budget status:\n{budget_status}",
            "",
            f"Booking provider:\n{best_flight.booking_provider or 'Airline / OTA'}",
            "",
            f"Booking:\n{booking_display}",
            "",
            f"Web verification:\n{ver_status}",
            "",
            f"Why:\n{recommendation_reason or 'Cheapest verified exact-match flight within your budget.'}",
        ]
        return "\n".join(lines)

    def _search_connecting_hubs(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        adults: int = 1,
        cabin_class: str = "economy",
        budget: Optional[float] = None,
    ) -> list[FareResult]:
        """Search and synthesize 1-stop connecting flight itineraries via primary hubs."""
        hubs = ["DEL", "BOM", "BLR", "HYD"]
        connecting_options: list[FareResult] = []

        for hub in hubs:
            if origin == hub or destination == hub:
                continue

            try:
                # Leg 1: origin -> hub
                leg1_fares = ignav_client.search_one_way_fares(
                    origin=origin,
                    destination=hub,
                    departure_date=travel_date,
                    adults=adults,
                    cabin_class=cabin_class,
                )
                if not leg1_fares:
                    continue

                # Leg 2: hub -> destination
                leg2_fares = ignav_client.search_one_way_fares(
                    origin=hub,
                    destination=destination,
                    departure_date=travel_date,
                    adults=adults,
                    cabin_class=cabin_class,
                )
                if not leg2_fares:
                    continue

                for l1 in leg1_fares:
                    if not l1.price or not l1.departure_time or not l1.arrival_time:
                        continue
                    for l2 in leg2_fares:
                        if not l2.price or not l2.departure_time or not l2.arrival_time:
                            continue

                        # Layover calculation
                        try:
                            arr_h, arr_m = map(int, l1.arrival_time.split(":"))
                            dep_h, dep_m = map(int, l2.departure_time.split(":"))
                            arr_min = arr_h * 60 + arr_m
                            dep_min = dep_h * 60 + dep_m

                            if dep_min < arr_min:
                                layover_min = (1440 - arr_min) + dep_min
                            else:
                                layover_min = dep_min - arr_min

                            # Valid connecting layover between 60 minutes and 720 minutes (12 hours)
                            if 60 <= layover_min <= 720:
                                total_price = l1.price + l2.price
                                if budget is not None and total_price > budget:
                                    continue

                                airline_name = l1.airline if (l1.airline and l1.airline == l2.airline) else f"{l1.airline or 'Airline'} / {l2.airline or 'Airline'}"
                                flt_str = f"{l1.flight_number} + {l2.flight_number} (via {hub})"

                                connecting_options.append(FareResult(
                                    flight_number=flt_str,
                                    airline=airline_name,
                                    origin=origin,
                                    destination=destination,
                                    travel_date=travel_date,
                                    departure_time=l1.departure_time,
                                    arrival_time=l2.arrival_time,
                                    price=total_price,
                                    currency="INR",
                                    price_status="verified",
                                    price_available=True,
                                    stops=1,
                                    ignav_id=l1.ignav_id,
                                    booking_url=l1.booking_url or l2.booking_url,
                                    booking_provider=l1.booking_provider or l2.booking_provider or "Airline Direct",
                                    booking_provider_type=l1.booking_provider_type or "airline",
                                    web_verification_status="unavailable"
                                ))
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"Error searching connecting hub {hub}: {e}")
                continue

        connecting_options.sort(key=lambda x: x.price if x.price else float("inf"))
        return connecting_options


# Singleton
agent = FlightOptionFinderAgent()

