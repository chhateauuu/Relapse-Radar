# Relapse Radar — P5 Context

**Lane: Frontend — plan/onboarding + integration + polish lead.** You own `web/` (the plan & onboarding flow), you **steward `shared/`**, and you run the **integration glue** + final polish.

> **Your one job:** build the catch-plan/onboarding flow ("mark your risky places, choose your person, write your message"), keep `shared/` the single source of truth, and wire the whole app together so it feels finished.

> **✅ Status (P5 slice):** the **catch-plan onboarding + editor is built, verified end-to-end, and merged to `main`** (`web/`). Consent-first wizard (welcome → places → person → message → thresholds → review) writes a schema-valid `CatchPlan`, plus a full editor with **one-tap revoke** (pause/resume neutralizes the plan within the frozen contract; delete clears local + API). Wired to `GET/PUT /plan/{user_id}` with a localStorage/fixture fallback so it runs offline ("live API" vs "offline demo" badge). **Remaining:** the Phase-2 integration pass (waits on P1–P4 existing) and the whole-app polish/dry-runs. `shared/` stays frozen and guarded — no schema drift.

This file is **self-contained**: you (and your coding agent) should be able to build your whole slice from just this file. Full team doc lives at `docs/Relapse-Radar-Context.md` if you want the deep background.

---

## 1. What we're building (the 90-second version)

Relapse Radar is a **privacy-first, on-device early-warning app for people in addiction recovery.** It learns *your* normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan *you wrote while you were well* — reaches out through the **one person you chose to catch you** (your sponsor), with words you wrote yourself.

**One-liner:** *catches you in your worst moment, through the person you trust, using a plan you wrote in your best moment.*

Why it can win: the flagship attempt (Mindstrong, ~$160M) died because it sent alerts to overloaded **clinicians**, felt like surveillance, and targeted a vague "everyone." Recovery fixes all three — the **sponsor** is a ready-made opted-in catcher, self-monitoring is native to recovery, and **relapse is a literal event** with a steep 90-day high-risk cliff.

**The thesis your flow embodies — the "Ulysses contract":** while the user is well and clear, they **pre-write exactly what happens when they're not.** You're not surveilled by a company — you're caught by *your own advance plan, executed through a person you chose.* Your onboarding/plan editor is where the user authors that contract. It solves consent + recipient + workflow in one move — the three things Mindstrong got wrong — because **the user is the author of the intervention.**

---

## 2. Your slice (what done looks like)

You build, end to end:

1. **The catch-plan editor + onboarding** (`web/`) — ✅ **done** — a short, warm flow that writes a `CatchPlan`:
   - **"Mark your risky places"** — add geofences (label + location + radius).
   - **"Choose your person"** — add the circle (sponsor name + contact).
   - **"Write your message"** — the `message_template` the user authors *in their own words* while well.
   - **Set your thresholds** — RED for N sustained days, require-geofence toggle, self-nudge-first toggle.
2. **Steward `shared/`** (with P2) — the canonical `shared/contracts.md` + the four fixtures. You are the keeper of the **single source of truth**: when anyone needs a schema clarified or a fixture added, it goes through you, and you make sure all five slices mock against the same shapes.
3. **Front-end integration / glue** — wire `web → api → llm` as each comes online, swapping fixture reads for live `fetch` calls. You run the **Phase-2 wire-up** (the order is in §6).
4. **The whole-app polish pass** — typography, motion, spacing, and especially the **timing of the SMS moment**. Run the **demo dry-runs** so it feels finished on a projector.

**Done when:** a user can author a catch-plan end to end, the app is wired together (web ↔ api ↔ llm), and the demo is polished.

**Start immediately:** `shared/` contracts + fixtures (with P2), and the **plan editor + onboarding** against fixtures. None of that needs the API.

**You wait for:** the other slices to *exist* before the big integration pass — but `shared/`, the plan editor, and polish prep all start now.

---

## 3. The FROZEN contracts — you are the STEWARD ⭐

You and P2 keep these exact. **Nobody changes a schema without it going through `shared/` and being flagged to the team** — five slices depend on them matching. Canonical: `shared/contracts.md`; samples: `shared/fixtures/`.

**CatchPlan** — the shape your editor WRITES (your primary surface):
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

**FeatureRecord** — one user-day of signals (you steward the fixtures of these):
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

**RiskAssessment** — output of the brain (you steward `sample_assessment.json`):
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

**EscalationEvent** — emitted when the rules fire:
```json
{
  "user_id": "maya", "day": 70, "type": "notify_circle", "recipient": "Dana",
  "channel": "sms",
  "message": "If you get this, I'm having a hard night near somewhere risky — please call me.",
  "sent_at": "2026-06-23T22:14:00Z"
}
```
`state` ∈ `GREEN | AMBER | RED`; `type` ∈ `self_nudge | notify_circle`.

**The four fixtures you steward (in `shared/fixtures/`):**
- `maya_healthy.json` — FeatureRecord[] (healthy baseline)
- `maya_spiral.json` — FeatureRecord[] (the relapse spiral)
- `sample_assessment.json` — a RiskAssessment
- `sample_plan.json` — a CatchPlan

---

## 4. The API you'll wire (at integration)

P3 serves these. Your editor uses the plan endpoints; the integration pass wires the rest for P4.

| Method | Path | Body → Returns | You use it for |
|---|---|---|---|
| GET/PUT | `/plan/{user_id}` | CatchPlan | **load + save the plan from your editor** |
| POST | `/simulate/step` | `{FeatureRecord, RiskAssessment}` | wiring P4's slider |
| GET | `/timeline/{user_id}` | EscalationEvent[] | wiring the sponsor view |

---

## 5. Repo layout & stack

```
relapse-radar/
├── web/                # P4 (demo screen) + YOU (plan, onboarding, glue, polish)
├── shared/             # YOU steward this (with P2) = source of truth for schemas
│   ├── contracts.md
│   └── fixtures/       # maya_healthy.json, maya_spiral.json, sample_assessment.json, sample_plan.json
└── docs/
```

| Thing | Choice |
|---|---|
| Stack | **Node 20 · React + Vite + Tailwind** |
| Charts | Recharts (P4 owns the chart; you focus on forms/flow) |
| Naming | JSON keys are `snake_case`, canonical |
| Commits | prefix `web:` / `shared:` |
| Run | `npm run dev` (from `web/`) |

**You share `web/` with P4** — agree on component boundaries early. Rough split: **P4** = demo screen (shell, chart, controls, sponsor view); **you** = plan/onboarding editor + integration glue + polish. Keep components modular.

---

## 6. How you fit in the build order — you run the wire-up

```
Phase 0 contract gate → Phase 1 everyone parallel on mocks → Phase 2 integrate (you run it) → polish
```

- **Phase 0 — you + P2 run the contract gate:** produce/confirm `shared/contracts.md` + the four fixtures, get team sign-off. **This one step unblocks all five people.** No feature code before it.
- **Phase 1:** build the plan editor + onboarding against fixtures.
- **Phase 2 — you run the integration pass**, swapping mocks for real in this order:
  1. P1 `assess` → into P3's `/assess`.
  2. P2 simulator → into P3's `/simulate`.
  3. P3 API → P4 + P5 web (fixtures → live `fetch`).
  4. P3 `explain` / `checkin` → fills `explanation` → shows in P4.
  5. P3 escalation + Twilio → **real SMS on the sponsor phone**.
- **Then:** the whole-app polish pass + demo dry-runs.

**Coordination:** you're the **connective tissue** — pair with P4 (shared `web/`), sit with P2 on `shared/`, and integrate through P3's API. You also help drive the final shared tasks (demo storyboard, deck, ethics slide, rehearsal) once the build is integrated.

---

## 7. Paste this into your coding agent to start

> I'm building the **P5** slice of **Relapse Radar**, a privacy-first early-warning app for addiction recovery. I own the plan/onboarding flow in `web/` (React + Vite + Tailwind), I steward `shared/` (the frozen contracts + fixtures), and I run front-end integration + polish. My job: (1) a **catch-plan editor + short onboarding** that writes a `CatchPlan` — mark risky places (geofences), choose your person (circle/sponsor + contact), write your own message (`message_template`), set thresholds (RED for N sustained days, require-geofence, self-nudge-first); (2) keep `shared/contracts.md` + the four fixtures as the single source of truth so all five slices mock the same shapes; (3) **wire `web → api → llm`** at integration, swapping fixture reads for live `fetch` calls to `/plan/{user_id}`, `/simulate/step`, `/timeline/{user_id}`; (4) a whole-app **polish pass** (typography, motion, the SMS-moment timing) + demo dry-runs.
> Honor the JSON contracts in `shared/contracts.md` **exactly** — and since I steward them, never let a schema drift without flagging the team. Build the editor against `shared/fixtures/sample_plan.json` first; no API needed yet. Tone is warm, calm, consent-first — this is the user authoring their own "Ulysses contract" while well. Coordinate component boundaries with P4 who shares `web/`. Build only my slice. Never change a shared schema without flagging it. `web/` is currently empty (just a README): coordinate with P4 so **exactly one of us** scaffolds the Vite + React + Tailwind app and commits it before either builds. The four fixtures already exist and match the contract — as steward I guard them and keep healthy (days 60–63) / spiral (days 64–70) self-consistent. At integration the API is at `http://localhost:8000` and Vite at `http://localhost:5173` — confirm P3 enabled CORS or every browser `fetch` fails — and I wire in the Phase-2 dependency order, not all at once.

---

## 8. Gotchas — read before you build ⚠️

- **`web/` is just a README — there is no app yet.** Coordinate with P4: **exactly ONE of you runs `npm create vite@latest` + Tailwind setup, commits it, then both build inside.** Don't both scaffold.
- **The four fixtures already exist and already match the contract.** As `shared/` steward your job is to **guard** them — extend carefully, keep `maya_healthy` (days 60–63) and `maya_spiral` (days 64–70) self-consistent, and never let a schema drift. If P2's simulator regenerates fixtures, sanity-check the shapes before committing.
- **CORS is the first thing to check when wiring breaks.** API on `http://localhost:8000`, Vite on `http://localhost:5173` — if a browser `fetch` fails, confirm P3 added `CORSMiddleware` for the Vite origin before debugging anything else.
- **Wire in the Phase-2 dependency order** (P1 `assess` → P3 `/assess`; P2 simulator → P3 `/simulate`; P3 → web; `explain`/`checkin` → P4; escalation + Twilio → sponsor SMS) — integrate one link at a time, not all at once, so a break is easy to localize.

---

## 9. Working agreement

- Contracts are **frozen** — and you're the steward, so **guard them**; flag any change to the team.
- **Mock from `shared/fixtures/`**, integrate early, **freeze before polishing**.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- Ethics baked into your flow: **no coercion** (the plan is revocable in one tap), **data dignity** (on-device, user owns/deletes it), and it always **nudges the user first**. Acute risk routes to **988 / SAMHSA 1-800-662-HELP** — the radar is upstream of crisis.
