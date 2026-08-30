"""Script to generate the complete 15-section demonstration notebook.

Creates notebook/flight_agent_demo.ipynb demonstrating the end-to-end real pipeline.
"""

from pathlib import Path
import nbformat as nbf

NOTEBOOK_DIR = Path(__file__).resolve().parent / "notebook"
NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOK_PATH = NOTEBOOK_DIR / "flight_agent_demo.ipynb"


def create_demo_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12"
        }
    }

    cells = [
        # Title
        nbf.v4.new_markdown_cell(
            "# ✈️ T10 Flight Option Finder — Master Pipeline Demonstration\n\n"
            "This notebook demonstrates the **complete real pipeline** for the autonomous Flight Option Finder agent.\n\n"
            "**Pipeline Architecture:**\n"
            "1. Environment check & config\n"
            "2. Natural language user request\n"
            "3. Structured request extraction\n"
            "4. Internal airport resolution (City → IATA)\n"
            "5. AviationStack flight schedule query & capability verification\n"
            "6. Flight schedule results\n"
            "7. Ignav authoritative live fare query\n"
            "8. Raw fare results\n"
            "9. Deterministic matching engine\n"
            "10. Matched fare validation & status preservation\n"
            "11. Hard constraint & budget filtering\n"
            "12. Candidate preference ranking & decision\n"
            "13. Real booking link retrieval (Ignav booking-links API)\n"
            "14. Auxiliary Scrapling web verification\n"
            "15. Final recommendation presentation"
        ),

        # Section 1
        nbf.v4.new_markdown_cell("## 1. Environment Check & Configuration\nValidates presence of required API keys and masks credentials."),
        nbf.v4.new_code_cell(
            "import os, sys\n"
            "sys.path.insert(0, os.path.abspath('..'))\n"
            "from config import config\n\n"
            "print('Config Status:')\n"
            "print(repr(config))\n"
            "missing = config.validate(check_nvidia=False)\n"
            "if missing:\n"
            "    print(f'Warning: Missing keys: {missing}')\n"
            "else:\n"
            "    print('✓ Core configurations loaded and validated.')"
        ),

        # Section 2
        nbf.v4.new_markdown_cell("## 2. User Request\nDefine the user's natural language flight search query."),
        nbf.v4.new_code_cell(
            "user_query = 'Find me a flight from Delhi to Mumbai on September 24 under ₹8,000'\n"
            "print(f'User Query: \"{user_query}\"')"
        ),

        # Section 3
        nbf.v4.new_markdown_cell("## 3. Parsed Request\nExtract structured entities (origin, destination, date, budget, currency, cabin class)."),
        nbf.v4.new_code_cell(
            "from agent import agent\n\n"
            "search_req = agent.parse_user_query(user_query)\n"
            "print('Extracted Search Parameters:')\n"
            "for k, v in search_req.model_dump().items():\n"
            "    print(f'  - {k}: {v}')"
        ),

        # Section 4
        nbf.v4.new_markdown_cell("## 4. Airport Resolution\nResolve city names to standard 3-letter IATA codes internally."),
        nbf.v4.new_code_cell(
            "from airport_resolver import resolve_airport\n\n"
            "orig_res = resolve_airport(search_req.origin_city)\n"
            "dest_res = resolve_airport(search_req.destination_city)\n\n"
            "print(f'Origin: {search_req.origin_city} -> {orig_res.code} ({orig_res.airport_name})')\n"
            "print(f'Destination: {search_req.destination_city} -> {dest_res.code} ({dest_res.airport_name})')"
        ),

        # Section 5
        nbf.v4.new_markdown_cell("## 5. AviationStack Search & Capability Verification\nQuery AviationStack and verify account plan capability for requested date."),
        nbf.v4.new_code_cell(
            "from tools import search_flights\n\n"
            "flights_resp = search_flights(\n"
            "    origin=orig_res.code,\n"
            "    destination=dest_res.code,\n"
            "    travel_date=search_req.travel_date\n"
            ")\n"
            "print(f'AviationStack Status: {flights_resp.get(\"status\")}')\n"
            "if flights_resp.get('message'):\n"
            "    print(f'Note: {flights_resp.get(\"message\")}')"
        ),

        # Section 6
        nbf.v4.new_markdown_cell("## 6. Flight Schedule Results\nInspect retrieved flight options."),
        nbf.v4.new_code_cell(
            "flights = flights_resp.get('flights', [])\n"
            "print(f'Retrieved {len(flights)} flight schedule records.')\n"
            "for f in flights[:5]:\n"
            "    print(f'  {f.get(\"airline\")} {f.get(\"flight_number\")} | {f.get(\"origin\")}->{f.get(\"destination\")} | {f.get(\"departure_time\")}->{f.get(\"arrival_time\")}')"
        ),

        # Section 7
        nbf.v4.new_markdown_cell("## 7. Ignav Fare Search\nFetch real, authoritative fares and itinerary segments from Ignav."),
        nbf.v4.new_code_cell(
            "from ignav_client import ignav_client\n\n"
            "raw_fares = ignav_client.search_one_way_fares(\n"
            "    origin=orig_res.code,\n"
            "    destination=dest_res.code,\n"
            "    departure_date=search_req.travel_date,\n"
            "    adults=search_req.passengers,\n"
            "    cabin_class=search_req.cabin_class,\n"
            ")\n"
            "print(f'Retrieved {len(raw_fares)} live fares from Ignav.')"
        ),

        # Section 8
        nbf.v4.new_markdown_cell("## 8. Fare Results\nDisplay raw fares retrieved from Ignav."),
        nbf.v4.new_code_cell(
            "for fare in raw_fares[:5]:\n"
            "    print(f'  {fare.airline} {fare.flight_number} | {fare.origin}->{fare.destination} | {fare.departure_time}->{fare.arrival_time} | ₹{fare.price:,.0f} [{fare.price_status.upper()}] | ID: {fare.ignav_id[:16]}...')"
        ),

        # Section 9
        nbf.v4.new_markdown_cell("## 9. Matching Engine\nExecute deterministic matching rules (AviationStack flight schedules ⟷ Ignav fares)."),
        nbf.v4.new_code_cell(
            "from matching import match_flights_with_fares\n"
            "from models import FlightOption\n\n"
            "# Run matching engine\n"
            "flight_objs = [FlightOption(**f) for f in flights] if flights else []\n"
            "if flight_objs:\n"
            "    matched_fares = match_flights_with_fares(flight_objs, raw_fares)\n"
            "else:\n"
            "    # Fallback to direct Ignav itineraries when flight schedules are restricted on free tier\n"
            "    matched_fares = raw_fares\n\n"
            "print(f'Matched options total: {len(matched_fares)}')"
        ),

        # Section 10
        nbf.v4.new_markdown_cell("## 10. Verified Fare Results\nInspect matched fare outcomes and status preservation."),
        nbf.v4.new_code_cell(
            "verified_count = sum(1 for f in matched_fares if f.price_status == 'verified')\n"
            "unverified_count = sum(1 for f in matched_fares if f.price_status == 'unverified')\n"
            "print(f'Verified Fares: {verified_count} | Unverified Fares: {unverified_count}')"
        ),

        # Section 11
        nbf.v4.new_markdown_cell("## 11. Budget Filtering\nEnforce deterministic hard constraint: price <= budget."),
        nbf.v4.new_code_cell(
            "budget = search_req.budget or 8000.0\n"
            "valid_candidates = [f for f in matched_fares if f.price_available and f.price is not None and f.price <= budget]\n"
            "print(f'Valid options within budget (≤ ₹{budget:,.0f}): {len(valid_candidates)}')\n"
            "for c in valid_candidates[:5]:\n"
            "    print(f'  ✓ {c.airline} {c.flight_number}: ₹{c.price:,.0f} ({c.departure_time} - {c.arrival_time})')"
        ),

        # Section 12
        nbf.v4.new_markdown_cell("## 12. Decision & Ranking\nRank valid candidates by verification status, preferences, price, and duration."),
        nbf.v4.new_code_cell(
            "best_flight = None\n"
            "if valid_candidates:\n"
            "    valid_candidates.sort(key=lambda x: (0 if x.price_status == 'verified' else 1, x.price if x.price else float('inf')))\n"
            "    best_flight = valid_candidates[0]\n"
            "    print(f'Top Selected Flight: {best_flight.airline} {best_flight.flight_number} at ₹{best_flight.price:,.0f} [{best_flight.price_status.upper()}]')\n"
            "else:\n"
            "    print('No candidates satisfied all criteria.')"
        ),

        # Section 13
        nbf.v4.new_markdown_cell("## 13. Booking Link Retrieval\nFetch real provider booking link from Ignav via `POST /api/fares/booking-links` using `ignav_id`."),
        nbf.v4.new_code_cell(
            "booking_opt = None\n"
            "if best_flight and best_flight.ignav_id:\n"
            "    booking_opts = ignav_client.get_booking_links(best_flight.ignav_id)\n"
            "    print(f'Retrieved {len(booking_opts)} booking options:')\n"
            "    for opt in booking_opts:\n"
            "        print(f'  - Provider: {opt.provider} ({opt.provider_type}) | URL: {opt.url[:70]}...')\n"
            "    if booking_opts:\n"
            "        booking_opt = booking_opts[0]\n"
            "        best_flight.booking_url = booking_opt.url\n"
            "        best_flight.booking_provider = booking_opt.provider"
        ),

        # Section 14
        nbf.v4.new_markdown_cell("## 14. Scrapling Web Verification\nAuxiliary web inspection of the live booking page."),
        nbf.v4.new_code_cell(
            "from scraping.booking_verifier import booking_verifier\n\n"
            "if best_flight and best_flight.booking_url:\n"
            "    ver_result = booking_verifier.verify_booking_page(\n"
            "        booking_url=best_flight.booking_url,\n"
            "        expected_flight=best_flight,\n"
            "        expected_fare=best_flight.price\n"
            "    )\n"
            "    print(f'Web Verification Status: {ver_result.status.upper()}')\n"
            "    print(f'Details: {ver_result.details}')\n"
            "    best_flight.web_verification_status = ver_result.status\n"
            "else:\n"
            "    print('No booking URL available for web verification.')"
        ),

        # Section 15
        nbf.v4.new_markdown_cell("## 15. Final Recommendation Presentation\nRender formatted user recommendation following Section 40 specification."),
        nbf.v4.new_code_cell(
            "final_result = agent.run(user_query)\n"
            "print(final_result.formatted_response)"
        )
    ]

    nb.cells = cells
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Notebook generated successfully at {NOTEBOOK_PATH}")


if __name__ == "__main__":
    create_demo_notebook()
