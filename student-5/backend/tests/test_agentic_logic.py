import app

SPACES = [
    {"space_id": 1, "space_name": "A", "building": "Building 11", "room_number": "1", "max_capacity": 6,
     "space_type": "Group Study", "noise_level": "Quiet", "facilities": ["Whiteboard", "Power Outlets", "Monitor"],
     "accessibility": "Wheelchair Accessible", "opening_time": "08:00", "closing_time": "22:00"},
    {"space_id": 2, "space_name": "B", "building": "Building 2", "room_number": "2", "max_capacity": 10,
     "space_type": "Group Study", "noise_level": "Moderate", "facilities": ["Whiteboard", "Power Outlets"],
     "accessibility": "Wheelchair Accessible", "opening_time": "08:00", "closing_time": "22:00"},
]


def test_deterministic_plan_extracts_core_requirements():
    req = app.deterministic_plan("quiet room for 5 people with a whiteboard and monitor in building 11")
    assert req["capacity"] == 5
    assert req["building"] == "Building 11"
    assert req["noise_level"] == "Quiet"
    assert "Whiteboard" in req["facilities"]
    assert "Monitor" in req["facilities"]


def test_exact_match_selected():
    req = {"capacity": 5, "building": "Building 11", "space_type": None, "noise_level": "Quiet",
           "facilities": ["Whiteboard", "Monitor"], "accessibility_required": False, "required_time": None}
    evaluated, exact, hard = app.act(req, SPACES)
    mode, relaxed, ranked = app.adapt(evaluated, exact, hard)
    assert mode == "exact_matches"
    assert ranked[0]["space"]["space_id"] == 1


def test_adapt_relaxes_soft_preference_before_hard_constraint():
    req = {"capacity": 5, "building": "Building 99", "space_type": None, "noise_level": "Quiet",
           "facilities": ["Whiteboard", "Monitor"], "accessibility_required": False, "required_time": None}
    evaluated, exact, hard = app.act(req, SPACES)
    mode, relaxed, ranked = app.adapt(evaluated, exact, hard)
    assert mode == "relaxed_soft_preferences"
    assert "building" in relaxed
    assert ranked[0]["space"]["space_id"] == 1
