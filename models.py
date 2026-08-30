"""Domain models for T10 Flight Option Finder.

Strict Pydantic schemas representing flights, fares, search requests,
trace events, and verification results.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


class FlightOption(BaseModel):
    """Normalized flight model representing an individual schedule/flight."""

    flight_number: str = Field(..., description="Normalized flight number e.g. 6E327")
    airline: Optional[str] = Field(None, description="Airline name e.g. IndiGo")
    airline_code: Optional[str] = Field(None, description="2-letter IATA airline code e.g. 6E")
    origin: str = Field(..., description="Origin airport IATA code e.g. DEL")
    destination: str = Field(..., description="Destination airport IATA code e.g. BOM")
    travel_date: str = Field(..., description="Travel date in YYYY-MM-DD format")
    departure_time: Optional[str] = Field(None, description="Local departure time e.g. 08:10")
    arrival_time: Optional[str] = Field(None, description="Local arrival time e.g. 10:20")
    departure_timezone: Optional[str] = Field(None, description="Departure airport timezone")
    arrival_timezone: Optional[str] = Field(None, description="Arrival airport timezone")
    stops: int = Field(0, description="Number of stops")
    source: str = Field("AviationStack", description="Source of flight schedule data")


class FareResult(BaseModel):
    """Normalized fare model representing live pricing and match status."""

    flight_number: str = Field(..., description="Normalized flight number e.g. 6E327")
    airline: Optional[str] = Field(None, description="Airline name")
    airline_code: Optional[str] = Field(None, description="Airline code e.g. 6E")
    origin: str = Field(..., description="Origin airport IATA code e.g. DEL")
    destination: str = Field(..., description="Destination airport IATA code e.g. BOM")
    travel_date: str = Field(..., description="Travel date in YYYY-MM-DD format")
    departure_time: Optional[str] = Field(None, description="Departure time")
    arrival_time: Optional[str] = Field(None, description="Arrival time")

    price: Optional[float] = Field(None, description="Authoritative fare amount")
    currency: Optional[str] = Field(None, description="Currency e.g. INR")
    price_available: bool = Field(False, description="Whether an exact fare is available")
    price_status: Literal["verified", "unverified", "unavailable", "error"] = Field(
        "unavailable", description="Fare verification status"
    )

    ignav_id: Optional[str] = Field(None, description="Unique Ignav itinerary identifier")

    booking_url: Optional[str] = Field(None, description="Direct booking link")
    booking_provider: Optional[str] = Field(None, description="Booking provider name")
    booking_provider_type: Optional[str] = Field(None, description="Provider type e.g. airline, ota")

    source: str = Field("Ignav", description="Authoritative fare source")
    retrieved_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when fare was retrieved"
    )

    web_verification_status: Literal["passed", "partial", "unavailable", "failed"] = Field(
        "unavailable", description="Auxiliary web verification status"
    )
    web_verification_url: Optional[str] = Field(None, description="URL checked by Scrapling")
    stops: int = Field(0, description="Number of stops")


class SearchRequest(BaseModel):
    """Structured user flight search request."""

    origin_city: Optional[str] = Field(None, description="Origin city name")
    destination_city: Optional[str] = Field(None, description="Destination city name")
    origin_code: Optional[str] = Field(None, description="Origin IATA code")
    destination_code: Optional[str] = Field(None, description="Destination IATA code")
    travel_date: str = Field(..., description="Date in YYYY-MM-DD format")
    budget: Optional[float] = Field(None, description="Maximum budget amount")
    currency: str = Field("INR", description="Currency code")
    passengers: int = Field(1, description="Number of passengers")
    cabin_class: str = Field("economy", description="Cabin class: economy, premium_economy, business, first")
    preferred_airline: Optional[str] = Field(None, description="Preferred airline name or code")
    preferred_departure: Optional[str] = Field(None, description="Preferred time of day: morning, afternoon, evening, night")
    max_stops: Optional[int] = Field(None, description="Maximum allowed stops")


class BookingOption(BaseModel):
    """Booking option returned by Ignav booking links endpoint."""

    provider: str = Field(..., description="Provider name")
    provider_type: Optional[str] = Field(None, description="airline or ota")
    price: Optional[float] = Field(None, description="Provider price")
    currency: Optional[str] = Field(None, description="Provider currency")
    url: str = Field(..., description="Booking URL")


class ScrapingVerificationResult(BaseModel):
    """Result of auxiliary Scrapling booking page verification."""

    status: Literal["passed", "partial", "unavailable", "failed"] = Field(
        ..., description="Verification outcome"
    )
    url: Optional[str] = Field(None, description="URL inspected")
    extracted_provider: Optional[str] = Field(None, description="Provider extracted from page")
    extracted_flight_number: Optional[str] = Field(None, description="Flight number extracted")
    extracted_route: Optional[str] = Field(None, description="Route extracted")
    extracted_date: Optional[str] = Field(None, description="Date extracted")
    extracted_fare: Optional[float] = Field(None, description="Price extracted from page")
    details: Optional[str] = Field(None, description="Additional verification notes")


class AgentTraceStep(BaseModel):
    """Step in the agent's PLAN -> ACT -> OBSERVE -> EVALUATE -> DECIDE execution trace."""

    phase: Literal["PLAN", "ACT", "OBSERVE", "EVALUATE", "DECIDE"] = Field(
        ..., description="Trace phase"
    )
    content: str = Field(..., description="Explanation / reasoning / plan")
    tool_calls: Optional[list[dict]] = Field(None, description="Tools called during ACT phase")
    observations: Optional[str] = Field(None, description="Observation summary")


class FlightSearchResult(BaseModel):
    """Complete flight search result and execution artifact."""

    query: str = Field(..., description="Original user prompt")
    search_request: Optional[SearchRequest] = Field(None, description="Extracted search parameters")
    flights_found: list[FlightOption] = Field(default_factory=list, description="AviationStack flight schedules")
    fares_found: list[FareResult] = Field(default_factory=list, description="Ignav fares retrieved")
    matched_fares: list[FareResult] = Field(default_factory=list, description="Exact-matched flight fares")
    valid_candidates: list[FareResult] = Field(default_factory=list, description="Candidates within budget & constraints")
    best_flight: Optional[FareResult] = Field(None, description="Selected winning flight recommendation")
    booking_option: Optional[BookingOption] = Field(None, description="Selected booking option")
    web_verification: Optional[ScrapingVerificationResult] = Field(None, description="Scrapling verification result")
    trace: list[AgentTraceStep] = Field(default_factory=list, description="Transparent agent trace")
    recommendation_reason: Optional[str] = Field(None, description="Explanation for selection")
    suggestions: list[str] = Field(default_factory=list, description="Smart recommendations when no exact flight is found")
    formatted_response: str = Field(..., description="Final user-facing formatted response")
