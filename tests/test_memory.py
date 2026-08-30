"""Unit tests for SessionMemory."""

import pytest
from memory import SessionMemory


def test_session_memory_initialization():
    mem = SessionMemory()
    prefs = mem.get_preferences()
    assert prefs.budget is None
    assert prefs.currency == "INR"
    assert prefs.passengers == 1
    assert prefs.cabin_class == "economy"
    assert len(mem.turn_history) == 0


def test_session_memory_update_across_turns():
    mem = SessionMemory()

    # Turn 1: User specifies budget and departure time preference
    mem.update(budget=8000.0, preferred_departure="morning")
    p1 = mem.get_preferences()
    assert p1.budget == 8000.0
    assert p1.preferred_departure == "morning"
    assert p1.origin_city is None

    # Turn 2: User specifies route and date
    mem.update(origin_city="Delhi", destination_city="Mumbai", travel_date="2026-09-24")
    p2 = mem.get_preferences()
    # Preserves earlier preferences
    assert p2.budget == 8000.0
    assert p2.preferred_departure == "morning"
    assert p2.origin_city == "Delhi"
    assert p2.destination_city == "Mumbai"
    assert p2.travel_date == "2026-09-24"


def test_session_memory_turn_history():
    mem = SessionMemory()
    mem.record_turn("Find me a flight to Mumbai", "Found IndiGo 6E327", {"flight": "6E327"})
    assert len(mem.turn_history) == 1
    assert mem.turn_history[0]["user_query"] == "Find me a flight to Mumbai"
    assert mem.turn_history[0]["agent_response"] == "Found IndiGo 6E327"


def test_session_memory_clear():
    mem = SessionMemory()
    mem.update(budget=5000.0)
    mem.record_turn("Hi", "Hello")
    mem.clear()
    assert mem.get_preferences().budget is None
    assert len(mem.turn_history) == 0
