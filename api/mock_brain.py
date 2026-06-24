"""Heuristic mock brain — fallback only.   [P3, replaced by P1+P2]

When `brain.assess` isn't importable yet, this derives a plausible
RiskAssessment from a FeatureRecord by comparing each signal to the healthy
baseline. It is NOT the real model — it exists so the API, rules engine, and the
whole demo flow light up end-to-end before P1 (risk) and P2 (state/drivers/
change-point) land. Swap happens automatically once `brain.assess` imports.
"""
from __future__ import annotations

import math
from typing import Any

# Healthy baseline (mean) and a rough spread per signal, mirrored from the
# simulator's BASELINE. (value - mean) / spread gives a z-like deviation.
_BASELINE = {
    "sleep_hours": (7.2, 0.5),
    "late_night_min": (8.0, 8.0),
    "screen_time_min": (210.0, 30.0),
    "unlocks": (78.0, 12.0),
    "outgoing_msgs": (18.0, 4.0),
    "unique_contacts": (6.0, 1.5),
    "location_entropy": (1.45, 0.2),
    "time_at_home_pct": (0.55, 0.08),
    "dwell_flagged_min": (0.0, 4.0),
    "steps": (5200.0, 700.0),
}

# Which direction is the "bad"/risk-increasing one for each signal.
_RISK_DIRECTION = {
    "sleep_hours": "down",
    "late_night_min": "up",
    "screen_time_min": "up",
    "unlocks": "up",
    "outgoing_msgs": "down",
    "unique_contacts": "down",
    "location_entropy": "down",
    "time_at_home_pct": "up",
    "dwell_flagged_min": "up",
    "steps": "down",
}


def assess(feature_record: dict[str, Any]) -> dict[str, Any]:
    features = feature_record.get("features", {})
    drivers = []
    risk_load = 0.0

    for name, (mean, spread) in _BASELINE.items():
        if name not in features:
            continue
        z = (float(features[name]) - mean) / spread
        direction = "up" if z > 0 else "down"
        # Only the risk-increasing direction adds to the load.
        if direction == _RISK_DIRECTION[name] and abs(z) > 1.0:
            risk_load += abs(z)
            drivers.append({"feature": name, "z": round(z, 2), "direction": direction})

    drivers.sort(key=lambda d: abs(d["z"]), reverse=True)
    drivers = drivers[:3]

    risk = 1.0 / (1.0 + math.exp(-(risk_load - 4.0)))  # logistic squash
    if risk >= 0.6:
        state = "RED"
    elif risk >= 0.3:
        state = "AMBER"
    else:
        state = "GREEN"

    return {
        "user_id": feature_record.get("user_id", "unknown"),
        "day": feature_record.get("day", 0),
        "risk": round(risk, 2),
        "state": state,
        "drivers": drivers,
        "changepoint": {"active": state != "GREEN", "started_day": None},
        "explanation": None,
    }
