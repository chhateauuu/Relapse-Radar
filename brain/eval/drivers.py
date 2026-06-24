"""Top risk drivers for a FeatureRecord.   [P2]

Returns the handful of signals pushing a person off their own baseline, in the
RiskAssessment `drivers` shape: [{feature, z, direction}, ...].

  - NOW: z-scores vs a population baseline (works today, no model needed).
  - LATER: SHAP over P1's LightGBM, against each user's PERSONAL baseline. The
    return shape is identical, so `assess()` keeps calling `drivers()` unchanged
    — only the internals swap. See the `_TODO_shap` note below.

Run a smoke test from the repo root:  python -m brain.eval.drivers
"""
from __future__ import annotations

from typing import Any

# (mean, spread) per signal. Mirrors the simulator's BASELINE; this is the
# stop-gap population baseline. P1 replaces it with the learned, per-user
# rolling baseline (median / IQR) — at which point `z` becomes "how far off
# is today from YOUR normal," which is the whole personalization story.
BASELINE: dict[str, tuple[float, float]] = {
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

# The risk-increasing direction for each signal (the "bad" way to deviate).
RISK_DIRECTION: dict[str, str] = {
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

MIN_ABS_Z = 1.0  # ignore signals within ~1 sd of normal


def drivers(feature_record: dict[str, Any], top_k: int = 3) -> list[dict[str, Any]]:
    """Top-k signals deviating in the risk-increasing direction, by |z|."""
    feats = feature_record.get("features", {})
    found: list[dict[str, Any]] = []
    for name, (mean, spread) in BASELINE.items():
        if name not in feats or spread == 0:
            continue
        z = (float(feats[name]) - mean) / spread
        direction = "up" if z > 0 else "down"
        if direction == RISK_DIRECTION[name] and abs(z) >= MIN_ABS_Z:
            found.append({"feature": name, "z": round(z, 2), "direction": direction})
    found.sort(key=lambda d: abs(d["z"]), reverse=True)
    return found[:top_k]


if __name__ == "__main__":
    import json
    from pathlib import Path

    fixtures = Path(__file__).resolve().parents[2] / "shared" / "fixtures"
    spiral = json.loads((fixtures / "maya_spiral.json").read_text(encoding="utf-8"))
    worst = spiral[-1]  # deepest day of the spiral
    result = drivers(worst)
    print(f"drivers for day {worst['day']}:")
    print(json.dumps(result, indent=2))
    assert result, "expected at least one driver on the worst spiral day"
    assert all({"feature", "z", "direction"} <= d.keys() for d in result), result
    print("OK:", ", ".join(d["feature"] for d in result))
