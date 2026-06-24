"""Deterministic catch-plan rules engine.   [P3]

This is the safety logic, and it is **pure rules by design** — never a model.
The system must never have a black box decide to text someone's sponsor; the
user authored this escalation ladder while well, and we execute it exactly.

Given a CatchPlan and the rolling history of RiskAssessments, decide whether to
escalate and — if so — whether to nudge the user first (`self_nudge`) or notify
their chosen person (`notify_circle`).

See ../shared/contracts.md for CatchPlan / RiskAssessment / EscalationEvent.
"""
from __future__ import annotations

from typing import Any, TypedDict

# Severity ordering so a "RED" threshold also fires on anything >= RED.
STATE_ORDER = {"GREEN": 0, "AMBER": 1, "RED": 2}


class Decision(TypedDict):
    triggered: bool
    type: str | None            # "self_nudge" | "notify_circle" | None
    reason: str
    recipient: str | None
    contact: str | None
    channel: str | None
    message: str | None
    sustained_met: bool
    geofence_met: bool
    sustained_days_seen: int


def _state_meets(state: str, threshold: str) -> bool:
    return STATE_ORDER.get(state, 0) >= STATE_ORDER.get(threshold, 99)


def sustained_met(
    assessments: list[dict[str, Any]], threshold_state: str, sustained_days: int
) -> tuple[bool, int]:
    """True iff the most recent `sustained_days` assessments all meet the
    threshold state. Returns (met, count_of_trailing_days_meeting_threshold)."""
    streak = 0
    for a in reversed(assessments):
        if _state_meets(a.get("state", "GREEN"), threshold_state):
            streak += 1
        else:
            break
    return (streak >= max(1, sustained_days), streak)


def geofence_met(plan: dict[str, Any], latest_record: dict[str, Any] | None) -> bool:
    """When the plan requires it, escalation only fires if the user is spending
    time near a place they flagged (dwell_flagged_min > 0)."""
    if not plan.get("require_geofence"):
        return True
    if latest_record is None:
        return False
    return float(latest_record.get("features", {}).get("dwell_flagged_min", 0)) > 0


def evaluate(
    plan: dict[str, Any],
    history: list[dict[str, Any]],
    already_nudged: bool = False,
) -> Decision:
    """Apply the user's catch-plan to the rolling history.

    history: list of {"record": FeatureRecord, "assessment": RiskAssessment}
             in day order. The last item is "today".
    already_nudged: whether a `self_nudge` already fired for this episode (so we
             progress to `notify_circle` instead of nudging again).
    """
    thresholds = plan.get("thresholds", {})
    threshold_state = thresholds.get("state", "RED")
    sustained_days = int(thresholds.get("sustained_days", 1))

    assessments = [h["assessment"] for h in history]
    latest_record = history[-1]["record"] if history else None

    sustained_ok, streak = sustained_met(assessments, threshold_state, sustained_days)
    geo_ok = geofence_met(plan, latest_record)

    base: Decision = {
        "triggered": False,
        "type": None,
        "reason": "",
        "recipient": None,
        "contact": None,
        "channel": None,
        "message": None,
        "sustained_met": sustained_ok,
        "geofence_met": geo_ok,
        "sustained_days_seen": streak,
    }

    if not assessments:
        base["reason"] = "no assessments yet"
        return base

    if not sustained_ok:
        base["reason"] = (
            f"risk not sustained: {streak}/{sustained_days} trailing days at "
            f">= {threshold_state}"
        )
        return base

    if not geo_ok:
        base["reason"] = "require_geofence is set but no dwell near a flagged place"
        return base

    # Threshold + geofence both satisfied -> escalate.
    if plan.get("self_nudge_first", True) and not already_nudged:
        base["triggered"] = True
        base["type"] = "self_nudge"
        base["recipient"] = plan.get("user_id", "user")
        base["channel"] = "push"
        base["message"] = (
            "Your line's been off for a few days near somewhere you flagged. "
            "Take a breath — want to do a quick check-in or call someone?"
        )
        base["reason"] = (
            f"sustained {streak}d at >= {threshold_state} + geofence -> nudging you first"
        )
        return base

    circle = plan.get("circle", [])
    recipient = circle[0] if circle else {}
    base["triggered"] = True
    base["type"] = "notify_circle"
    base["recipient"] = recipient.get("name", "your circle")
    base["contact"] = recipient.get("contact")
    base["channel"] = "sms"
    base["message"] = plan.get(
        "message_template",
        "If you get this, I'm having a hard night — please call me.",
    )
    base["reason"] = (
        f"sustained {streak}d at >= {threshold_state} + geofence -> notifying circle"
    )
    return base
