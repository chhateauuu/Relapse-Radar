# Relapse Radar — P3 Context

**Lane: Backend — API + LLM + escalation.** You own `api/` and `llm/`.

> **Your one job:** be the hub. Wrap the brain in a FastAPI, run the **deterministic catch-plan rules engine**, fire a **real SMS via Twilio** to the sponsor phone, and provide the **LLM** explanation + check-in. The whole demo flows through you.

This file is **self-contained**: you (and your coding agent) should be able to build your whole slice from just this file. Full team doc lives at `docs/Relapse-Radar-Context.md` if you want the deep background.

---

## 1. What we're building (the 90-second version)

Relapse Radar is a **privacy-first, on-device early-warning app for people in addiction recovery.** It learns *your* normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan *you wrote while you were well* — reaches out through the **one person you chose to catch you** (your sponsor), with words you wrote yourself.

**One-liner:** *catches you in your worst moment, through the person you trust, using a plan you wrote in your best moment.*

Why it can win: the flagship attempt (Mindstrong, ~$160M) died because it sent alerts to overloaded **clinicians**, felt like surveillance, and targeted a vague "everyone." Recovery fixes all three — the **sponsor** is a ready-made opted-in catcher, self-monitoring is native to recovery, and **relapse is a literal event** with a steep 90-day high-risk cliff.

**The three layers — you own two of them:**

| Layer | What it is | Real AI? | Owner |
|---|---|---|---|
| **Escalation / geofence / thresholds** | "if RED for 2 days AND near a flagged place → text sponsor" | **No — deterministic by design (this is YOU)** | **P3** |
| The "is your line off?" engine | detect deviation from *your own* normal, score risk, find change-point | Yes — the real ML | P1 + P2 |
| **The empathic interface** | explain the risk in plain words, run the check-in | **Generative AI as interface (this is YOU)** | **P3** |

> Critical framing for judges: **the escalation is deliberately deterministic.** The system must *never* have a black-box AI deciding to text someone's sponsor. User-authored, rules-based safety logic is a **feature**, not a shortcut. The LLM is the *empathy* layer, not the predictor.

---

## 2. Your slice (what done looks like)

You build, end to end:

1. **FastAPI** (`api/`) exposing all the endpoints in §3. `/assess` imports `brain.assess` (mock with `shared/fixtures/sample_assessment.json` until P1 ships). *A working skeleton already exists in `api/main.py` with fixture fallbacks — extend it.*
2. **The deterministic catch-plan rules engine** — reads a `CatchPlan`, applies its thresholds (`state` == RED, `sustained_days`) + geofence requirement + self-nudge-first logic, and decides **`self_nudge`** vs **`notify_circle`**. Pure rules, no ML.
3. **Twilio SMS** + `/escalate` + `/timeline` — when the rule fires `notify_circle`, send a **real SMS** (Twilio free-trial number is fine) to the sponsor's phone with the user's pre-written message. Record `EscalationEvent`s and serve them on `/timeline`.
4. **The LLM layer** (`llm/`) — `explain(assessment) -> sentence` turns the `drivers` into a kind, non-clinical line; `checkin() -> sentence` is a HALT-style motivational-interviewing check-in. Expose them as endpoints that fill `RiskAssessment.explanation`. *Canned-text stubs already exist in `llm/llm.py` — swap in a real API call (OpenAI/Anthropic); note Ollama as the on-device privacy-story prod path.*

**Done when:** the web can drive a full **healthy → spiral → escalation** run through your API, a **real text lands** on the sponsor phone, and explanations come back in human language.

**Start immediately (all mockable — no hard deps):** the FastAPI skeleton returning fixtures, the rules engine, Twilio wiring, and the LLM calls. You don't need P1/P2 to build any of it — mock `assess` with the fixture and the simulator with the fixture arrays.

**You wait for:** P1's real `assess` and P2's simulator — swap your mocks for real imports at integration (Phase 2). The contract shapes don't change, so the swap is a one-liner each.

---

## 3. The FROZEN contracts — honor these EXACTLY ⭐

You touch **all four** shapes plus the endpoint table — you're the hub. **Do not change a schema without flagging the team.** Canonical: `shared/contracts.md`; samples: `shared/fixtures/`.

**FeatureRecord** — one user-day of signals (input to `/assess`):
```json
{
  "user_id": "maya", "day": 67, "date": "2026-06-23",
  "features": {
    "sleep_hours": 7.2, "late_night_min": 5, "screen_time_min": 210, "unlocks": 78,
    "outgoing_msgs": 18, "unique_contacts": 6, "location_entropy": 1.4,
    "time_at_home_pct": 0.55, "dwell_flagged_min": 0, "steps": 5200
  },
  "label": null
}
```

**RiskAssessment** — output of `assess()`; **your LLM fills `explanation`**:
```json
{
  "user_id": "maya", "day": 70, "risk": 0.81, "state": "RED",
  "drivers": [
    { "feature": "sleep_hours", "z": -2.3, "direction": "down" },
    { "feature": "dwell_flagged_min", "z": 4.0, "direction": "up" },
    { "feature": "outgoing_msgs", "z": -2.4, "direction": "down" }
  ],
  "changepoint": { "active": true, "started_day": 67 },
  "explanation": null
}
```
`state` ∈ `GREEN | AMBER | RED`.

**CatchPlan** — the user-authored escalation config your rules engine READS (P5 edits it):
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

**EscalationEvent** — what your rules engine EMITS (and `/timeline` serves):
```json
{
  "user_id": "maya", "day": 70, "type": "notify_circle", "recipient": "Dana",
  "channel": "sms",
  "message": "If you get this, I'm having a hard night near somewhere risky — please call me.",
  "sent_at": "2026-06-23T22:14:00Z"
}
```
`type` ∈ `self_nudge | notify_circle`.

**API endpoints — YOUR surface to build:**

| Method | Path | Body → Returns | Notes |
|---|---|---|---|
| POST | `/assess` | FeatureRecord → RiskAssessment | wraps `brain.assess` |
| POST | `/assess/batch` | FeatureRecord[] → RiskAssessment[] | replay/demo |
| GET/PUT | `/plan/{user_id}` | CatchPlan | P5 edits it |
| POST | `/simulate/start` | `{user_id, scenario}` → ok | P4 drives demo; serves P2's simulator |
| POST | `/simulate/step` | → `{FeatureRecord, RiskAssessment}` | the slider |
| POST | `/escalate` | (internal) → EscalationEvent | rules engine → Twilio |
| GET | `/timeline/{user_id}` | → EscalationEvent[] | demo timeline |

---

## 4. Repo layout (your corner)

```
relapse-radar/
├── brain/
│   └── assess.py       # P1 — you import assess() from here (mock until ready)
├── simulator/          # P2 — you serve this via /simulate (mock with fixtures until ready)
├── api/                # YOU — FastAPI; wraps brain.assess; rules engine; Twilio
│   └── main.py         #   skeleton with fixture fallbacks already exists — extend it
├── llm/                # YOU — explain + check-in (importable + endpoints)
│   └── llm.py          #   canned-text stubs already exist — swap in a real call
├── shared/
│   ├── contracts.md
│   └── fixtures/       # mock everything from here: sample_assessment.json, sample_plan.json, maya_*.json
└── docs/
```

---

## 5. Stack & conventions

| Thing | Choice |
|---|---|
| Language | **Python 3.11** |
| Your libs | **FastAPI** · uvicorn · the **Twilio** SDK · an LLM client (**openai**/anthropic) behind one wrapper in `llm/` |
| LLM prod path | on-device **Ollama** (Phi-3 / Llama 3.2) — note it for the privacy story; API call is fine for the demo |
| Secrets | Twilio + LLM keys via **env vars / `.env`**, never commit them |
| Naming | JSON keys + Python both `snake_case` |
| Commits | prefix `api:` / `llm:` |
| Run | `uvicorn api.main:app --reload` (from repo root) |

Install: `pip install -r requirements.txt` from repo root.

**Security note:** keep raw data on-device in the product story — the API only ever transmits the **risk state** and the **message the user authored**, and only when the user's own rule fires. Don't log message content; don't commit secrets; validate request bodies.

---

## 6. How you fit in the build order

```
contracts → P1 model + P2 sim → P3 API (you, the hub) → P4/P5 web → demo
```

You are **the hub everyone integrates through.** Phase 2 swap order (P5 runs the wire-up, but it lands in your API):

1. P1 `assess` → into your `/assess` (replace the mock import).
2. P2 simulator → into your `/simulate/start` + `/simulate/step`.
3. Your API → P4 + P5 web (they move from fixture reads to live fetches).
4. Your `explain` / `checkin` → fills `explanation` → P4 displays it.
5. Your escalation + Twilio → **real SMS on the sponsor phone** (the demo money shot).

**Coordination:** you're the integration hub — keep your endpoints stable and fixture-compatible so P4/P5 never block on you. Pair with P5 (who runs the Phase-2 wire-up).

---

## 7. Paste this into your coding agent to start

> I'm building the **P3** slice of **Relapse Radar**, a privacy-first early-warning app for addiction recovery. I own `api/` and `llm/`. My job: (1) a **FastAPI** exposing `/assess`, `/assess/batch`, `/plan/{user_id}` (GET/PUT), `/simulate/start`, `/simulate/step`, `/escalate`, `/timeline/{user_id}`, wrapping `brain.assess` (mock with `shared/fixtures/sample_assessment.json` until P1 ships); (2) a **deterministic catch-plan rules engine** that reads a CatchPlan and decides `self_nudge` vs `notify_circle` from thresholds (state==RED, sustained_days) + geofence + self-nudge-first; (3) **Twilio** SMS on `notify_circle` → a real text to the sponsor, recorded as EscalationEvents served on `/timeline`; (4) an **LLM** layer in `llm/` — `explain(assessment)` (drivers → kind non-clinical sentence) and `checkin()` (HALT-style), filling `RiskAssessment.explanation`.
> Honor the JSON contracts in `shared/contracts.md` **exactly** (FeatureRecord, RiskAssessment, CatchPlan, EscalationEvent, and the endpoint table). Mock all my dependencies from `shared/fixtures/`. Keep Twilio/LLM keys in env vars, never commit secrets, never log message content. The escalation must be purely deterministic — no AI decides to text anyone. Build only my slice. Never change a shared schema without flagging it. Critical: add FastAPI `CORSMiddleware` for the Vite origin `http://localhost:5173` or the browser can't call the API; Twilio trial accounts can only SMS *verified* numbers, so verify the sponsor phone and keep a non-SMS fallback; load secrets from a `.env` (add `python-dotenv` + a committed `.env.example`, gitignore `.env`), never commit keys, never log message content; run `uvicorn` from the repo root and keep the existing stub fallback so the API boots without the brain.

---

## 8. Gotchas — read before you build ⚠️

- **Enable CORS or the browser literally cannot reach you.** The web app runs on Vite at `http://localhost:5173`; your API runs at `http://localhost:8000`. Add FastAPI `CORSMiddleware` allowing the Vite origin **on day one** — otherwise every P4/P5 `fetch` fails at integration. This is the #1 integration killer.
- **Twilio trial numbers can only text *verified* numbers.** Verify the sponsor's phone in the Twilio console before the demo, or the "real text" silently fails. **Keep a fallback** (a second browser window / on-screen alert) so a Twilio hiccup can't sink the money shot.
- **Secrets live in `.env`, never in git.** Add `python-dotenv`, load keys from env, commit a `.env.example` with empty placeholders, and add `.env` to `.gitignore`.
- **Run `uvicorn api.main:app --reload` from the repo root** so `from brain.assess import assess` resolves. Keep the skeleton's `try/except` stub fallback so the API still boots if the brain isn't ready yet.
- **Never log message content** (the user's catch-plan text) — privacy is the entire pitch. Only ever transmit the risk state + the message the user authored, and only when their own rule fires.

---

## 9. Working agreement

- Contracts are **frozen** — flag before changing.
- **Mock your dependencies** (`shared/fixtures/`), integrate early, keep endpoints stable so the frontend never blocks on you.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- Acute risk routes to **988 / SAMHSA 1-800-662-HELP** — the radar is *upstream* of crisis, not a crisis line. Always self-nudge the user first before any escalation.
