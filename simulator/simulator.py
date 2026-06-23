"""Simulator — synthetic healthy baseline + injectable relapse spiral.   [P2]

Emits FeatureRecords (see ../shared/contracts.md). Drives the live demo: the
front-end slider steps through these days. This is a skeleton — tune the
day-by-day spiral curves so the demo feels real.
"""
from __future__ import annotations

import random
from typing import Any

# A healthy person's typical day (the baseline the app "learns").
BASELINE: dict[str, float] = {
    "sleep_hours": 7.2,
    "late_night_min": 5,
    "screen_time_min": 210,
    "unlocks": 78,
    "outgoing_msgs": 18,
    "unique_contacts": 6,
    "location_entropy": 1.4,
    "time_at_home_pct": 0.55,
    "dwell_flagged_min": 0,
    "steps": 5200,
}


def _record(user_id: str, day: int, features: dict[str, float], label: int) -> dict[str, Any]:
    return {"user_id": user_id, "day": day, "date": None,
            "features": {k: round(v, 2) for k, v in features.items()}, "label": label}


def healthy_day(user_id: str, day: int) -> dict[str, Any]:
    """A normal day: baseline +/- a little noise."""
    f = {k: v * random.uniform(0.95, 1.05) for k, v in BASELINE.items()}
    return _record(user_id, day, f, 0)


def spiral_day(user_id: str, day: int, t: float) -> dict[str, Any]:
    """A day during the relapse spiral. t in [0, 1] = how far in.

    TODO(P2): tune these curves; they're the heart of the demo.
    """
    f = dict(BASELINE)
    f["sleep_hours"] = 7.2 - 3.1 * t          # 7.2 -> 4.1
    f["late_night_min"] = 5 + 90 * t          # 5 -> 95
    f["screen_time_min"] = 210 + 150 * t
    f["unlocks"] = 78 + 87 * t
    f["outgoing_msgs"] = 18 - 15 * t          # withdrawal
    f["unique_contacts"] = 6 - 5 * t
    f["location_entropy"] = 1.4 - 1.1 * t     # isolating
    f["time_at_home_pct"] = 0.55 + 0.35 * t
    f["dwell_flagged_min"] = 22 * t           # drifting to a risky place
    f["steps"] = 5200 - 3400 * t
    return _record(user_id, day, f, 1)


def run(user_id: str = "maya", healthy_days: int = 60, spiral_days: int = 7):
    """Yield a full healthy -> spiral stream of FeatureRecords."""
    for d in range(healthy_days):
        yield healthy_day(user_id, d)
    for i in range(spiral_days):
        yield spiral_day(user_id, healthy_days + i, t=(i + 1) / spiral_days)


if __name__ == "__main__":
    import json

    for rec in run():
        print(json.dumps(rec))
