"""In-memory backend state.   [P3]

A tiny process-local store so the API is stateful within a demo run without a
database. Holds: the per-user CatchPlan, the rolling history of
(FeatureRecord, RiskAssessment) pairs, the escalation timeline, and the active
simulator session. Swap for real persistence post-hackathon.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent.parent / "shared" / "fixtures"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# user_id -> CatchPlan
_plans: dict[str, dict[str, Any]] = {}

# user_id -> [{"record": FeatureRecord, "assessment": RiskAssessment}, ...] (day order)
_history: dict[str, list[dict[str, Any]]] = {}

# user_id -> [EscalationEvent, ...]
_timeline: dict[str, list[dict[str, Any]]] = {}

# user_id -> {"scenario": str, "cursor": int, "records": [FeatureRecord, ...]}
_sessions: dict[str, dict[str, Any]] = {}


def get_plan(user_id: str) -> dict[str, Any]:
    """Return the user's CatchPlan, seeding from the sample fixture on first read."""
    if user_id not in _plans:
        plan = load_fixture("sample_plan.json")
        plan["user_id"] = user_id
        _plans[user_id] = plan
    return _plans[user_id]


def set_plan(user_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    plan = dict(plan)
    plan["user_id"] = user_id
    _plans[user_id] = plan
    return plan


def history(user_id: str) -> list[dict[str, Any]]:
    return _history.setdefault(user_id, [])


def record_step(user_id: str, record: dict[str, Any], assessment: dict[str, Any]) -> None:
    """Append one observed day + its assessment to the rolling history."""
    history(user_id).append({"record": record, "assessment": assessment})


def reset_history(user_id: str) -> None:
    _history[user_id] = []
    _timeline[user_id] = []


def timeline(user_id: str) -> list[dict[str, Any]]:
    return _timeline.setdefault(user_id, [])


def add_event(user_id: str, event: dict[str, Any]) -> None:
    timeline(user_id).append(event)


def session(user_id: str) -> dict[str, Any] | None:
    return _sessions.get(user_id)


def set_session(user_id: str, scenario: str, records: list[dict[str, Any]]) -> None:
    _sessions[user_id] = {"scenario": scenario, "cursor": 0, "records": records}
