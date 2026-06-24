"""Simulator — synthetic healthy baseline + injectable relapse spiral.   [P2]

Emits FeatureRecords (see ../shared/contracts.md). Drives the live demo: the
front-end slider steps through these days, and the API's "synthetic" scenario
streams `run()` straight into /simulate.

Reproducible by default (seeded), so the demo line looks identical every run.
The spiral is an *accelerating* drift — gentle for a day or two, then steep —
which is both more realistic and a fair test of the change-point detector.
"""
from __future__ import annotations

import random
from typing import Any, Iterator, Optional

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

# Where each signal lands at the deepest point of the spiral (t = 1).
SPIRAL_TARGET: dict[str, float] = {
    "sleep_hours": 4.1,        # sleep collapses
    "late_night_min": 95,      # up all night
    "screen_time_min": 360,    # doomscrolling
    "unlocks": 165,            # restless
    "outgoing_msgs": 3,        # social withdrawal
    "unique_contacts": 1,      # isolating
    "location_entropy": 0.3,   # routine collapse
    "time_at_home_pct": 0.9,   # holed up
    "dwell_flagged_min": 22,   # drifting to a risky place
    "steps": 1800,             # lethargy
}

# Integer-valued signals (counts / minutes) -> rounded to whole numbers.
_COUNT_KEYS = {
    "late_night_min", "screen_time_min", "unlocks",
    "outgoing_msgs", "unique_contacts", "dwell_flagged_min", "steps",
}

# Floors so noise can never push a signal to something nonsensical.
_FLOORS: dict[str, float] = {
    "unique_contacts": 1, "outgoing_msgs": 0, "dwell_flagged_min": 0, "steps": 0,
}


def _clean(features: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in features.items():
        v = max(v, _FLOORS.get(k, 0.0))
        out[k] = int(round(v)) if k in _COUNT_KEYS else round(v, 2)
    return out


def _record(user_id: str, day: int, features: dict[str, float], label: int) -> dict[str, Any]:
    return {"user_id": user_id, "day": day, "date": None,
            "features": _clean(features), "label": label}


def _noise(rng: random.Random, scale: float = 0.04) -> float:
    return 1.0 + rng.uniform(-scale, scale)


def _ease(t: float) -> float:
    """Accelerating ease-in: visible early drift, then steeper (convex)."""
    t = max(0.0, min(1.0, t))
    return 0.4 * t + 0.6 * t * t


def healthy_day(user_id: str, day: int, rng: Optional[random.Random] = None) -> dict[str, Any]:
    """A normal day: baseline ± a little noise."""
    rng = rng or random
    f = {k: v * _noise(rng) for k, v in BASELINE.items()}
    return _record(user_id, day, f, 0)


def spiral_day(user_id: str, day: int, t: float, rng: Optional[random.Random] = None) -> dict[str, Any]:
    """A day during the relapse spiral. t in [0, 1] = how far in.

    Each signal interpolates from its baseline toward SPIRAL_TARGET along an
    accelerating curve, with light noise.
    """
    rng = rng or random
    e = _ease(t)
    f = {k: (base + (SPIRAL_TARGET[k] - base) * e) * _noise(rng, 0.03)
         for k, base in BASELINE.items()}
    return _record(user_id, day, f, 1)


def run(
    user_id: str = "maya",
    healthy_days: int = 60,
    spiral_days: int = 7,
    start_day: int = 0,
    seed: int = 42,
) -> Iterator[dict[str, Any]]:
    """Yield a full healthy -> spiral stream of FeatureRecords (reproducible)."""
    rng = random.Random(seed)
    day = start_day
    for _ in range(healthy_days):
        yield healthy_day(user_id, day, rng)
        day += 1
    for i in range(spiral_days):
        yield spiral_day(user_id, day, t=(i + 1) / spiral_days, rng=rng)
        day += 1


def series(**kwargs: Any) -> list[dict[str, Any]]:
    """Convenience: the whole run as a list (handy for tests / notebooks)."""
    return list(run(**kwargs))


if __name__ == "__main__":
    import json

    # A compact arc that mirrors the fixtures: 4 healthy (days 60-63) then the
    # 7-day spiral (days 64-70).
    for rec in run(healthy_days=4, spiral_days=7, start_day=60):
        print(json.dumps(rec))
