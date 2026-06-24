"""End-to-end demo pipeline: FeatureRecord stream -> full RiskAssessments.   [P2]

`assess()` (P1 risk + P2 state/drivers) scores ONE day in isolation, so it can't
know when a sustained drift *started* — that needs the risk *series*. This module
streams records, accumulates the per-day risk, and runs `brain.eval.detect` over
the series so far to fill `changepoint.started_day` on each day.

This is the exact integration P3/P4 use for the live demo: replay the whole arc
with `assess_stream(records)`, or keep a running list and call `detect` each step
as the slider advances. Output is the frozen RiskAssessment shape.

Run:  python -m brain.eval.pipeline   (replays the maya healthy -> spiral arc)
"""
from __future__ import annotations

from typing import Any, Iterable

from brain.assess import assess
from brain.eval.detect import detect


def assess_stream(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score a stream of FeatureRecords, filling change-point over the series.

    Each returned RiskAssessment has `risk` (P1), `drivers` (P2), and a `state` +
    `changepoint` computed by the change-point detector over the running risk
    series — so `changepoint.started_day` reflects the real onset, not `null`.
    """
    out: list[dict[str, Any]] = []
    risks: list[float] = []
    days: list[int] = []
    for record in records:
        assessment = assess(record)  # P1 risk + P2 drivers (+ per-day state)
        risks.append(assessment["risk"])
        days.append(assessment.get("day", len(days)))
        cp = detect(risks, days)  # change-point over the series so far
        assessment["state"] = cp["state"]
        assessment["changepoint"] = cp["changepoint"]
        out.append(assessment)
    return out


if __name__ == "__main__":
    import json
    from pathlib import Path

    fixtures = Path(__file__).resolve().parents[2] / "shared" / "fixtures"
    records: list[dict[str, Any]] = []
    for name in ("maya_healthy.json", "maya_spiral.json"):
        records += json.loads((fixtures / name).read_text(encoding="utf-8"))

    assessments = assess_stream(records)
    print("day  risk   state  onset  drivers")
    for a in assessments:
        cp = a["changepoint"]
        onset = cp["started_day"] if cp["active"] else "-"
        top = ", ".join(d["feature"] for d in a["drivers"]) or "-"
        print(f"{a['day']:>3}  {a['risk']:.3f}  {a['state']:<5}  {str(onset):>5}  {top}")

    assert any(a["state"] == "RED" for a in assessments), "expected RED days"
    assert any(a["changepoint"]["active"] for a in assessments), "expected an active changepoint"
    onset = next(a["changepoint"]["started_day"] for a in assessments if a["changepoint"]["active"])
    print(f"OK: full pipeline — risk + state + drivers + change-point onset (day {onset})")
