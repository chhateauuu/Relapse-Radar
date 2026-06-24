"""Relapse Radar API.   [P3]

The integration hub. Wraps the brain's `assess`, fills the LLM explanation,
serves the simulator to the demo, runs the deterministic catch-plan rules, and
fires the real Twilio SMS. Exposes every endpoint in ../shared/contracts.md and
falls back to fixtures/stubs where P1/P2 aren't ready, so the frontend can
integrate today.

Run from the repo root:  uvicorn api.main:app --reload
Docs:                    http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Optional .env loading for Twilio / LLM creds (no hard dependency).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

from . import escalation, rules, simulate, store

# Brain core. By default import the real `brain.assess` (P1+P2). Set
# USE_MOCK_BRAIN=1 to force the heuristic mock — handy for a lively end-to-end
# demo before P1/P2 ship their model. Either way the swap is automatic later.
if os.getenv("USE_MOCK_BRAIN", "").lower() in ("1", "true", "yes"):
    from .mock_brain import assess
else:
    try:
        from brain.assess import assess
    except Exception:  # pragma: no cover - integration safety net
        from .mock_brain import assess

# LLM empathy layer; fall back to a no-op if the module isn't importable.
try:
    from llm.llm import checkin as llm_checkin
    from llm.llm import explain as llm_explain
except Exception:  # pragma: no cover
    def llm_explain(assessment: dict[str, Any]) -> str:
        return ""

    def llm_checkin() -> str:
        return "HALT check: hungry, angry, lonely, or tired?"


app = FastAPI(title="Relapse Radar API", version="0.1.0")

# The web demo (P4/P5) runs on a different origin; allow it to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _assess_and_explain(feature_record: dict[str, Any]) -> dict[str, Any]:
    """Run the brain, then fill RiskAssessment.explanation via the LLM layer."""
    assessment = assess(feature_record)
    try:
        assessment["explanation"] = llm_explain(assessment)
    except Exception:  # pragma: no cover - explanation is best-effort
        assessment["explanation"] = None
    return assessment


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/")
def root():
    return {"ok": True, "service": "relapse-radar"}


# --------------------------------------------------------------------------- #
# Assess (wraps P1 + P2; P3 fills explanation)
# --------------------------------------------------------------------------- #
@app.post("/assess")
def post_assess(feature_record: dict[str, Any]):
    assessment = _assess_and_explain(feature_record)
    store.record_step(feature_record.get("user_id", "unknown"), feature_record, assessment)
    return assessment


@app.post("/assess/batch")
def post_assess_batch(feature_records: list[dict[str, Any]]):
    out = []
    for fr in feature_records:
        a = _assess_and_explain(fr)
        store.record_step(fr.get("user_id", "unknown"), fr, a)
        out.append(a)
    return out


# --------------------------------------------------------------------------- #
# Catch-plan (P5 edits it)
# --------------------------------------------------------------------------- #
@app.get("/plan/{user_id}")
def get_plan(user_id: str):
    return store.get_plan(user_id)


@app.put("/plan/{user_id}")
def put_plan(user_id: str, plan: dict[str, Any]):
    return store.set_plan(user_id, plan)


# --------------------------------------------------------------------------- #
# Simulator (P4 drives the demo slider)
# --------------------------------------------------------------------------- #
class SimulateStartBody(BaseModel):
    user_id: str = "maya"
    scenario: str | None = None


@app.post("/simulate/start")
def simulate_start(body: SimulateStartBody):
    return simulate.start(body.user_id, body.scenario)


class SimulateStepBody(BaseModel):
    user_id: str = "maya"


@app.post("/simulate/step")
def simulate_step(body: SimulateStepBody):
    sess = store.session(body.user_id)
    if sess is None:
        raise HTTPException(status_code=409, detail="call /simulate/start first")

    cursor = sess["cursor"]
    records = sess["records"]
    if cursor >= len(records):
        return {"done": True, "day": None, "record": None, "assessment": None}

    record = records[cursor]
    sess["cursor"] = cursor + 1

    assessment = _assess_and_explain(record)
    store.record_step(body.user_id, record, assessment)

    # Dry-run the rules so the frontend can light up when escalation is due.
    already_nudged = any(
        e["type"] == "self_nudge" for e in store.timeline(body.user_id)
    )
    decision = rules.evaluate(
        store.get_plan(body.user_id), store.history(body.user_id), already_nudged
    )

    return {
        "done": False,
        "day": record.get("day"),
        "record": record,
        "assessment": assessment,
        "rules": decision,
    }


# --------------------------------------------------------------------------- #
# Escalation (the real SMS)
# --------------------------------------------------------------------------- #
class EscalateBody(BaseModel):
    user_id: str = "maya"
    day: int | None = None
    send: bool = True  # set False for a dry run (evaluate without sending/recording)


@app.post("/escalate")
def escalate(body: EscalateBody):
    plan = store.get_plan(body.user_id)
    history = store.history(body.user_id)
    if not history:
        raise HTTPException(
            status_code=409,
            detail="no assessments yet; call /assess or /simulate/step first",
        )

    already_nudged = any(e["type"] == "self_nudge" for e in store.timeline(body.user_id))
    decision = rules.evaluate(plan, history, already_nudged)

    if not decision["triggered"]:
        return {"triggered": False, "decision": decision}

    day = body.day if body.day is not None else history[-1]["record"].get("day", 0)

    if not body.send:  # dry run: report what would happen, change nothing
        return {"triggered": True, "decision": decision, "dry_run": True}

    event = escalation.dispatch(body.user_id, day, decision)
    store.add_event(body.user_id, event)
    return event


@app.get("/timeline/{user_id}")
def get_timeline(user_id: str):
    return store.timeline(user_id)


# --------------------------------------------------------------------------- #
# Check-in (LLM empathy layer; additive, used by P4)
# --------------------------------------------------------------------------- #
@app.get("/checkin")
def checkin():
    return {"message": llm_checkin()}
