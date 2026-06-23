# Frozen contracts (source of truth)

These JSON shapes are the contract every slice codes against. **Do not change a schema without flagging the team** — five components depend on them matching exactly. Sample instances live in [`fixtures/`](fixtures/).

## FeatureRecord — one user-day of signals (input to the brain)
```json
{
  "user_id": "maya",
  "day": 67,
  "date": "2026-06-23",
  "features": {
    "sleep_hours": 7.2,
    "late_night_min": 5,
    "screen_time_min": 210,
    "unlocks": 78,
    "outgoing_msgs": 18,
    "unique_contacts": 6,
    "location_entropy": 1.4,
    "time_at_home_pct": 0.55,
    "dwell_flagged_min": 0,
    "steps": 5200
  },
  "label": null
}
```

## RiskAssessment — output of `brain.assess()`
```json
{
  "user_id": "maya",
  "day": 70,
  "risk": 0.81,
  "state": "RED",
  "drivers": [
    { "feature": "sleep_hours", "z": -2.3, "direction": "down" },
    { "feature": "dwell_flagged_min", "z": 4.0, "direction": "up" },
    { "feature": "outgoing_msgs", "z": -2.4, "direction": "down" }
  ],
  "changepoint": { "active": true, "started_day": 67 },
  "explanation": null
}
```
`state` is one of `GREEN | AMBER | RED`. `explanation` is filled by the LLM layer (P3). `risk` is filled by P1; `state`/`drivers`/`changepoint` by P2.

## CatchPlan — the user-authored escalation config
```json
{
  "user_id": "maya",
  "thresholds": { "state": "RED", "sustained_days": 2 },
  "require_geofence": true,
  "geofences": [{ "label": "old neighborhood", "lat": 0.0, "lng": 0.0, "radius_m": 200 }],
  "self_nudge_first": true,
  "circle": [{ "name": "Dana", "role": "sponsor", "contact": "+15555550123" }],
  "message_template": "If you get this, I'm having a hard night near somewhere risky — please call me."
}
```

## EscalationEvent — emitted when the rules fire
```json
{
  "user_id": "maya",
  "day": 70,
  "type": "notify_circle",
  "recipient": "Dana",
  "channel": "sms",
  "message": "If you get this, I'm having a hard night near somewhere risky — please call me.",
  "sent_at": "2026-06-23T22:14:00Z"
}
```
`type` is one of `self_nudge | notify_circle`.

## API endpoints (FastAPI)
| Method | Path | Body → Returns |
|---|---|---|
| POST | `/assess` | FeatureRecord → RiskAssessment |
| POST | `/assess/batch` | FeatureRecord[] → RiskAssessment[] |
| GET/PUT | `/plan/{user_id}` | CatchPlan |
| POST | `/simulate/start` | `{user_id, scenario}` → ok |
| POST | `/simulate/step` | → `{FeatureRecord, RiskAssessment}` |
| POST | `/escalate` | (internal) → EscalationEvent |
| GET | `/timeline/{user_id}` | → EscalationEvent[] |

## Fixtures
- `fixtures/maya_healthy.json` — FeatureRecord[] (healthy baseline)
- `fixtures/maya_spiral.json` — FeatureRecord[] (the relapse spiral)
- `fixtures/sample_assessment.json` — a RiskAssessment
- `fixtures/sample_plan.json` — a CatchPlan
