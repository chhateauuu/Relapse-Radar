# api/ — the backend (P3)

FastAPI hub the whole app integrates through. Wraps the brain's `assess`, fills
the LLM explanation, serves the simulator to the demo, runs the **deterministic
catch-plan rules engine**, and fires the **real Twilio SMS** (the demo's big
moment). Honors `../shared/contracts.md` exactly.

## Run it
```bash
pip install -r requirements.txt
# from the repo root:
uvicorn api.main:app --reload          # http://127.0.0.1:8000/docs

# Lively spiral demo before P1/P2 ship the real model:
USE_MOCK_BRAIN=1 uvicorn api.main:app --reload
```
Copy `.env.example` → `.env` for Twilio / OpenAI creds (gitignored). Without
them the API still runs fully: SMS is **simulated**, explanations are composed
locally.

## Endpoints (all JSON, contracts in `../shared/contracts.md`)
| Method | Path | Body → Returns | Notes |
|---|---|---|---|
| GET | `/` | → `{ok, service}` | health |
| POST | `/assess` | FeatureRecord → RiskAssessment | wraps brain; P3 fills `explanation` |
| POST | `/assess/batch` | FeatureRecord[] → RiskAssessment[] | replay |
| GET/PUT | `/plan/{user_id}` | CatchPlan | P5 edits it; seeded from `sample_plan.json` |
| POST | `/simulate/start` | `{user_id, scenario}` → `{ok, days}` | resets history |
| POST | `/simulate/step` | `{user_id}` → `{day, record, assessment, rules}` | the slider |
| POST | `/escalate` | `{user_id, day?, send?}` → EscalationEvent | the rules + SMS |
| GET | `/timeline/{user_id}` | → EscalationEvent[] | demo timeline |
| GET | `/checkin` | → `{message}` | HALT check-in (LLM) |

**Extras beyond the frozen contract (additive, safe to use):**
- `/simulate/step` also returns a `rules` block (a dry-run of the rules engine)
  so the frontend can light up the moment escalation is due.
- `/escalate` accepts `send: false` for a dry run (evaluate, change nothing) and
  returns `{triggered: false, decision}` when the plan's conditions aren't met.

## Scenarios for `/simulate/start`
`healthy` · `spiral` · `healthy_to_spiral` (default, the full arc) · `synthetic`
(streams P2's tuned simulator when available). Source = `../shared/fixtures`.

## The rules engine (`rules.py`) — pure, by design
Reads the CatchPlan + rolling assessment history and decides:
- **sustained:** the last `thresholds.sustained_days` assessments all at/above
  `thresholds.state` (GREEN < AMBER < RED).
- **geofence:** if `require_geofence`, today's `dwell_flagged_min > 0`.
- both met → `self_nudge` first (if `self_nudge_first`), then `notify_circle`.

No model ever decides to text someone — the user authored this ladder while well.

## Twilio (`escalation.py`)
`/escalate` builds the EscalationEvent and, for `notify_circle`, sends the user's
pre-written message via Twilio. Needs `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_FROM_NUMBER` in `.env`; otherwise it returns a `delivery.simulated`
event so the flow still demos offline.

## Files
`main.py` endpoints · `rules.py` rules engine · `escalation.py` Twilio + events ·
`simulate.py` scenario sessions · `store.py` in-memory state · `mock_brain.py`
heuristic fallback (replaced by `brain.assess`).

## Integration (§B8)
`/assess` imports `brain.assess` (P1+P2) — swap is automatic once it ships.
`synthetic` scenario imports `simulator.simulator.run` (P2). Until then,
everything runs on `../shared/fixtures` + the mock brain.
