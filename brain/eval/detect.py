"""Change-point + state detection over a personal risk series.   [P2]

P1's model produces a per-day `risk` in [0, 1]. This module turns the *series*
of those daily risks into the two fields P2 owns on a RiskAssessment:

  - `state`        : GREEN | AMBER | RED   (from the latest risk)
  - `changepoint`  : {active, started_day}  (WHEN a sustained drift began)

The whole point is to separate **one bad night** from a **multi-day spiral**, so
the app never escalates on noise. `ruptures` (PELT) finds the breakpoint when
it's installed; a dependency-free CUSUM is the fallback so this always runs.

Run a smoke test from the repo root:  python -m brain.eval.detect
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

# Risk -> state thresholds. Kept in sync with the rest of the brain.
GREEN_MAX = 0.30   # risk < 0.30            -> GREEN
AMBER_MAX = 0.60   # 0.30 <= risk < 0.60    -> AMBER ; risk >= 0.60 -> RED

ELEVATED = 0.40    # a single day counts as "elevated" at/above this risk
MIN_SUSTAIN = 2    # need >= this many recent elevated days to call drift "active"


def state_for(risk: float) -> str:
    """Map a single risk value in [0, 1] to a traffic-light state."""
    if risk >= AMBER_MAX:
        return "RED"
    if risk >= GREEN_MAX:
        return "AMBER"
    return "GREEN"


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _cusum_onset(series: Sequence[float]) -> Optional[int]:
    """Dependency-free CUSUM: index where a sustained upward shift begins.

    Uses the early third of the series as the person's "normal," then walks a
    cumulative positive-drift sum; the onset is where that sum lifts off zero
    and never returns. Returns None if there is no sustained drift.
    """
    n = len(series)
    if n < MIN_SUSTAIN + 1:
        return None
    baseline = _mean(series[: max(1, n // 3)])
    slack = 0.05  # ignore drift smaller than this (noise tolerance)
    cum = 0.0
    onset: Optional[int] = None
    for i, x in enumerate(series):
        cum = max(0.0, cum + (x - baseline - slack))
        if cum > 0.0 and onset is None:
            onset = i
        elif cum == 0.0:
            onset = None  # drift reset -> the run wasn't sustained
    return onset


def _ruptures_onset(series: Sequence[float]) -> Optional[int]:
    """PELT breakpoint via `ruptures`, or None if it isn't installed / no shift."""
    try:
        import numpy as np
        import ruptures as rpt
    except Exception:
        return None
    if len(series) < MIN_SUSTAIN + 1:
        return None
    signal = np.asarray(series, dtype=float).reshape(-1, 1)
    bkps = rpt.Pelt(model="l2", min_size=1).fit(signal).predict(pen=0.5)
    # bkps are segment-END indices (the last one == len). Take the last real
    # breakpoint whose following segment is higher than what came before.
    for bk in reversed(bkps[:-1]):
        if 0 < bk < len(series) and _mean(series[bk:]) > _mean(series[:bk]):
            return bk
    return None


def detect(
    risk_series: Sequence[float],
    days: Optional[Sequence[int]] = None,
    use_ruptures: bool = True,
) -> dict[str, Any]:
    """Assess the latest day given the full personal risk series.

    Args:
        risk_series: per-day risk in [0, 1], oldest -> newest.
        days: matching day ids (defaults to 0..n-1); used for `started_day`.
        use_ruptures: try the ruptures breakpoint first, else CUSUM.

    Returns:
        {"state": "...", "changepoint": {"active": bool, "started_day": int|None}}
    """
    series = [float(r) for r in risk_series]
    if not series:
        return {"state": "GREEN", "changepoint": {"active": False, "started_day": None}}

    day_ids = list(days) if days is not None else list(range(len(series)))
    state = state_for(series[-1])

    onset = _ruptures_onset(series) if use_ruptures else None
    if onset is None:
        onset = _cusum_onset(series)

    recent_elevated = sum(1 for x in series[-MIN_SUSTAIN:] if x >= ELEVATED)
    active = (
        onset is not None
        and recent_elevated >= MIN_SUSTAIN
        and state != "GREEN"
    )
    started_day = day_ids[onset] if (active and onset is not None and 0 <= onset < len(day_ids)) else None

    return {"state": state, "changepoint": {"active": active, "started_day": started_day}}


if __name__ == "__main__":
    import json

    # A flat-healthy stretch (days 60-63) then a climbing spiral (days 64-70),
    # mirroring shared/fixtures. The detector should flag onset at day 64.
    healthy = [0.06, 0.08, 0.07, 0.05]
    spiral = [0.18, 0.30, 0.45, 0.58, 0.68, 0.75, 0.81]
    series = healthy + spiral
    day_ids = list(range(60, 60 + len(series)))

    result = detect(series, day_ids)
    print(json.dumps(result, indent=2))
    assert result["state"] == "RED", result
    assert result["changepoint"]["active"] is True, result
    # CUSUM lands on 64 (first lift-off); ruptures/PELT on 65 (segment boundary).
    # Both are correct within +/-1 day of the true onset (day 64).
    assert 64 <= result["changepoint"]["started_day"] <= 66, result
    print("OK: detected RED, drift onset ~ day", result["changepoint"]["started_day"])
