"""Session Memory module for T10 Flight Option Finder.

Tracks user preferences, active search constraints, and conversation context across turns.
Never stores API keys or credentials.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User preferences remembered across conversational turns."""

    budget: Optional[float] = Field(None, description="Maximum budget amount")
    currency: str = Field("INR", description="Preferred currency code")
    preferred_airline: Optional[str] = Field(None, description="Preferred airline name or code")
    preferred_departure: Optional[str] = Field(None, description="e.g. morning, afternoon, evening, night")
    origin_city: Optional[str] = Field(None, description="Origin city")
    destination_city: Optional[str] = Field(None, description="Destination city")
    origin_code: Optional[str] = Field(None, description="Origin IATA code")
    destination_code: Optional[str] = Field(None, description="Destination IATA code")
    travel_date: Optional[str] = Field(None, description="Travel date YYYY-MM-DD")
    cabin_class: str = Field("economy", description="Cabin class")
    passengers: int = Field(1, description="Number of passengers")
    max_stops: Optional[int] = Field(None, description="Maximum stops")


class SessionMemory:
    """Manages conversational session state and preference persistence."""

    def __init__(self):
        self.preferences = UserPreferences()
        self.turn_history: list[dict[str, Any]] = []

    def update(
        self,
        budget: Optional[float] = None,
        currency: Optional[str] = None,
        preferred_airline: Optional[str] = None,
        preferred_departure: Optional[str] = None,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        origin_code: Optional[str] = None,
        destination_code: Optional[str] = None,
        travel_date: Optional[str] = None,
        cabin_class: Optional[str] = None,
        passengers: Optional[int] = None,
        max_stops: Optional[int] = None,
    ) -> UserPreferences:
        """Update active session preferences with non-None values."""
        if budget is not None:
            self.preferences.budget = budget
        if currency is not None:
            self.preferences.currency = currency
        if preferred_airline is not None:
            self.preferences.preferred_airline = preferred_airline
        if preferred_departure is not None:
            self.preferences.preferred_departure = preferred_departure
        if origin_city is not None:
            self.preferences.origin_city = origin_city
        if destination_city is not None:
            self.preferences.destination_city = destination_city
        if origin_code is not None:
            self.preferences.origin_code = origin_code
        if destination_code is not None:
            self.preferences.destination_code = destination_code
        if travel_date is not None:
            self.preferences.travel_date = travel_date
        if cabin_class is not None:
            self.preferences.cabin_class = cabin_class
        if passengers is not None:
            self.preferences.passengers = passengers
        if max_stops is not None:
            self.preferences.max_stops = max_stops

        return self.preferences

    def record_turn(self, user_query: str, agent_response: str, metadata: Optional[dict] = None) -> None:
        """Record a completed interaction turn into memory."""
        self.turn_history.append({
            "turn_index": len(self.turn_history) + 1,
            "user_query": user_query,
            "agent_response": agent_response,
            "metadata": metadata or {},
        })

    def get_preferences(self) -> UserPreferences:
        """Retrieve the current user preferences."""
        return self.preferences

    def clear(self) -> None:
        """Reset memory state."""
        self.preferences = UserPreferences()
        self.turn_history.clear()

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory state to dict."""
        return {
            "preferences": self.preferences.model_dump(),
            "turns_count": len(self.turn_history),
            "history": self.turn_history,
        }
