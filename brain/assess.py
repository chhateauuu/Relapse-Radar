"""assess(feature_record) -> RiskAssessment   [P1 + P2]

The single function every other slice imports. See ../shared/contracts.md.
  - P1 fills `risk` (population baseline + trained model, in brain/scorer.py).
  - P2 fills `state`, `changepoint`, `drivers` (brain/eval: change-point + drivers).

Contract (FROZEN): a FeatureRecord dict in, a RiskAssessment dict out. The import
is cheap and has NO hard ML dependency, so P3 can import it at API startup and it
degrades gracefully if the trained model or P2's eval module isn't available.
"""
from __future__ import annotations

from typing import Any

from brain import scorer

# P2 owns state / changepoint / drivers via brain.eval. Import defensively so a
# missing or broken eval module can never take down `assess` (and therefore the
# whole API). Safe, contract-valid defaults stand in until eval is importable.
try:
    from brain.eval import drivers as _eval_drivers
    from brain.eval import state_for as _eval_state_for
except Exception:  # pragma: no cover - integration safety net
    _eval_drivers = None
    _eval_state_for = None


def _state_for(risk: float) -> str:
    """Traffic-light state for a single day's risk (P2's thresholds)."""
    if _eval_state_for is not None:
        try:
            return _eval_state_for(risk)
        except Exception:
            pass
    if risk >= 0.60:
        return "RED"
    if risk >= 0.30:
        return "AMBER"
    return "GREEN"


def _drivers(feature_record: dict[str, Any]) -> list[dict[str, Any]]:
    """Top risk drivers in the contract shape [{feature, z, direction}]."""
    if _eval_drivers is not None:
        try:
            return _eval_drivers(feature_record)
        except Exception:
            pass
    # Fallback: derive drivers from the same population baseline scorer uses.
    features = feature_record.get("features", {}) or {}
    found: list[dict[str, Any]] = []
    for name, z in scorer.zscores(features).items():
        direction = "up" if z > 0 else "down"
        if direction == scorer.RISK_DIRECTION[name] and abs(z) >= 1.0:
            found.append({"feature": name, "z": round(z, 2), "direction": direction})
    found.sort(key=lambda d: abs(d["z"]), reverse=True)
    return found[:3]


def assess(feature_record: dict[str, Any]) -> dict[str, Any]:
    """Map one FeatureRecord -> one RiskAssessment (frozen contract shape)."""
    risk = scorer.risk(feature_record)
    state = _state_for(risk)

    # `assess` scores one day in isolation; a sustained-drift onset needs the
    # risk *series*, which P3 owns (it stores history and can call
    # brain.eval.detect over it). Here we report the per-day change-point view.
    changepoint = {"active": state != "GREEN", "started_day": None}

    return {
        "user_id": feature_record.get("user_id", "unknown"),
        "day": feature_record.get("day", 0),
        "risk": round(risk, 3),
        "state": state,
        "drivers": _drivers(feature_record),
        "changepoint": changepoint,
        "explanation": None,
    }


if __name__ == "__main__":
    import json
    from pathlib import Path

    fixtures = Path(__file__).resolve().parent.parent / "shared" / "fixtures"
    for name in ("maya_healthy.json", "maya_spiral.json"):
        records = json.loads((fixtures / name).read_text(encoding="utf-8"))
        print(f"\n# {name}")
        for rec in records:
            ra = assess(rec)
            top = ", ".join(d["feature"] for d in ra["drivers"]) or "-"
            print(f"  day {ra['day']:>3}  risk={ra['risk']:.3f}  {ra['state']:<5}  [{top}]")
