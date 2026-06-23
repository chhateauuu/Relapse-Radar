"""assess(feature_record) -> RiskAssessment   [P1 + P2]

The single function every other slice imports. See ../shared/contracts.md.
  - P1 fills `risk` (personal baseline + LightGBM model).
  - P2 fills `state`, `changepoint`, `drivers` (change-point detector + SHAP).

This stub returns valid, schema-correct placeholder data so P3/P4/P5 can
integrate immediately. Replace the internals as P1 and P2 land their pieces.
"""
from __future__ import annotations

from typing import Any


def assess(feature_record: dict[str, Any]) -> dict[str, Any]:
    """Map one FeatureRecord -> one RiskAssessment (placeholder)."""
    # TODO(P1): baseline z-scores -> LightGBM -> risk
    # TODO(P2): change-point -> state + started_day ; SHAP -> drivers
    return {
        "user_id": feature_record.get("user_id", "unknown"),
        "day": feature_record.get("day", 0),
        "risk": 0.08,
        "state": "GREEN",
        "drivers": [],
        "changepoint": {"active": False, "started_day": None},
        "explanation": None,
    }


if __name__ == "__main__":
    import json
    from pathlib import Path

    sample = json.loads(
        (Path(__file__).resolve().parent.parent / "shared" / "fixtures" / "maya_spiral.json").read_text(encoding="utf-8")
    )[-1]
    print(json.dumps(assess(sample), indent=2))
