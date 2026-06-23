"""Relapse Radar API.   [P3]

Wraps brain.assess, runs the deterministic catch-plan rules, fires Twilio, and
exposes the endpoints in ../shared/contracts.md. Falls back to fixtures/stubs
where P1/P2 aren't ready, so the frontend can integrate today.

Run from the repo root:  uvicorn api.main:app --reload
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

# Import the brain core; fall back to a local stub if it isn't ready yet.
try:
    from brain.assess import assess
except Exception:  # pragma: no cover - integration safety net
    def assess(feature_record: dict) -> dict:
        return {
            "user_id": feature_record.get("user_id", "unknown"),
            "day": feature_record.get("day", 0),
            "risk": 0.08, "state": "GREEN", "drivers": [],
            "changepoint": {"active": False, "started_day": None},
            "explanation": None,
        }

app = FastAPI(title="Relapse Radar API")
FIXTURES = Path(__file__).resolve().parent.parent / "shared" / "fixtures"


def _fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@app.get("/")
def root():
    return {"ok": True, "service": "relapse-radar"}


@app.post("/assess")
def post_assess(feature_record: dict):
    return assess(feature_record)


@app.post("/assess/batch")
def post_assess_batch(feature_records: list[dict]):
    return [assess(fr) for fr in feature_records]


@app.get("/plan/{user_id}")
def get_plan(user_id: str):
    return _fixture("sample_plan.json")


@app.put("/plan/{user_id}")
def put_plan(user_id: str, plan: dict):
    # TODO(P3): persist the CatchPlan
    return {"ok": True, "plan": plan}


@app.get("/timeline/{user_id}")
def get_timeline(user_id: str):
    # TODO(P3): real EscalationEvent history
    return []

# TODO(P3): /simulate/start, /simulate/step (serve P2's simulator),
#           the catch-plan rules engine, /escalate -> Twilio SMS.
