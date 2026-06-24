# Relapse Radar — P4 Context

**Lane: Frontend — the live-demo screen.** You own `web/` (the shell, the "your line" chart, the demo controls, the sponsor view).

> **Your one job:** build the screen the judges watch. Slide the spiral forward → the line climbs → the state flips GREEN→AMBER→RED → the sponsor's phone lights up. This is the emotional money shot.

This file is **self-contained**: you (and your coding agent) should be able to build your whole slice from just this file. Full team doc lives at `docs/Relapse-Radar-Context.md` if you want the deep background.

---

## 1. What we're building (the 90-second version)

Relapse Radar is a **privacy-first, on-device early-warning app for people in addiction recovery.** It learns *your* normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan *you wrote while you were well* — reaches out through the **one person you chose to catch you** (your sponsor), with words you wrote yourself.

**One-liner:** *catches you in your worst moment, through the person you trust, using a plan you wrote in your best moment.*

Why it can win: the flagship attempt (Mindstrong, ~$160M) died because it sent alerts to overloaded **clinicians**, felt like surveillance, and targeted a vague "everyone." Recovery fixes all three — the **sponsor** is a ready-made opted-in catcher, self-monitoring is native to recovery, and **relapse is a literal event** with a steep 90-day high-risk cliff.

**The tone matters in your UI:** strengths-based, **no shaming.** It's not a judgmental "relapse score" — it's *"your line."* Calm, warm, "you're on track" by default. The design principle: always nudge *you* first; never surveillance.

---

## 2. The demo you're building (the money shot)

Two phone screens side by side — **Maya's phone** + **her sponsor's phone** — and a slider labeled **"advance days."**

1. **Green state.** Maya, 67 days sober. "Your line" sits steady inside her normal band. On-device indicator lit.
2. **Slide forward.** Signals visibly degrade — sleep bar drops, late-night spikes, comms thin out, mobility shrinks. The line climbs to **AMBER**. Contributing signals light up.
3. **It explains itself** in plain words (from the LLM): *"You've slept under 5 hrs and gone quiet 3 days running — that's been a rough sign for you before."*
4. **It checks in** (LLM chat): *"Hey — noticing your line's off. HALT check: how are you?"* — Maya doesn't answer.
5. **She drifts near a flagged place** → state hits **RED + sustained** → her pre-written plan fires.
6. **The sponsor's phone buzzes** with the message Maya wrote in week 1: *"If you get this, I'm having a hard night near somewhere risky — please call me."*
7. **Punchline:** *"Nothing left her phone but one text she wrote to herself. No cloud, no doctor, no surveillance."*

**Two toggles for the technical audience (build these — they're proof):**
- **Personal vs Population** — flip it: the population model misses Maya or false-alarms; the personal model nails it.
- **On-device** — show that raw data never transmits; only the risk state + her message.

---

## 3. Your slice (what done looks like)

You build, end to end:

1. **The phone-styled shell** — looks like a real app on a projector (phone frame, status bar, clean type). Mobile-first, big and legible from the back of a room.
2. **The "your line" chart** (Recharts) — the signal/risk value vs the **personal normal band**, with the risk line **climbing** across days. The centerpiece visual.
3. **The GREEN / AMBER / RED indicator** + a **contributing-signals readout** (which signals are off, driven by `RiskAssessment.drivers`).
4. **The demo controls** — the **advance-day slider**, the **on-device** toggle, the **personal-vs-population** toggle.
5. **The sponsor companion view** — the second-phone screen showing the alert: *"Maya asked to be checked on if things looked rough. Now's the time. Call her."*

**Done when:** the full demo runs from the slider and looks clean on a projector — slide the spiral, the line climbs, the state flips, the sponsor screen lights up.

**Start immediately (no API needed — you're the longest frontend pole, start hour one):** build the entire UI against `shared/fixtures/maya_spiral.json` (an array of `FeatureRecord`s for the spiral) and `shared/fixtures/sample_assessment.json` (a `RiskAssessment`). The slider just indexes into the fixture array.

**You wait for:** nothing to start. At integration you swap fixture reads for live API calls (the shapes are identical, so it's a drop-in).

---

## 4. The FROZEN contracts — what you render ⭐

You consume two shapes (and read the plan for sponsor context). **Don't change a schema without flagging the team.** Canonical: `shared/contracts.md`; samples in `shared/fixtures/`.

**FeatureRecord** — one user-day; the slider steps through an array of these. Drives the signal bars:
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

**RiskAssessment** — what you render as the line + state + drivers + explanation:
```json
{
  "user_id": "maya", "day": 70, "risk": 0.81, "state": "RED",
  "drivers": [
    { "feature": "sleep_hours", "z": -2.3, "direction": "down" },
    { "feature": "dwell_flagged_min", "z": 4.0, "direction": "up" },
    { "feature": "outgoing_msgs", "z": -2.4, "direction": "down" }
  ],
  "changepoint": { "active": true, "started_day": 67 },
  "explanation": "You've slept less and gone quiet for 3 days — that's been a rough sign before."
}
```
- `risk` (0–1) → the climbing line. `state` → the GREEN/AMBER/RED indicator color.
- `drivers` → the "contributing signals" readout (each has a signed `z` + `direction` up/down).
- `changepoint.started_day` → mark on the timeline ("this started N days ago").
- `explanation` → the plain-language sentence (filled by the LLM; in fixtures it may be pre-written).

**EscalationEvent** — what the sponsor view shows when the plan fires (served by `GET /timeline/{user_id}`):
```json
{
  "user_id": "maya", "day": 70, "type": "notify_circle", "recipient": "Dana",
  "channel": "sms",
  "message": "If you get this, I'm having a hard night near somewhere risky — please call me.",
  "sent_at": "2026-06-23T22:14:00Z"
}
```

---

## 5. The API you'll call (at integration)

P3 serves these; until then, mock with fixtures. Shapes are identical, so swapping is a drop-in.

| Method | Path | Returns | You use it for |
|---|---|---|---|
| POST | `/simulate/start` | ok | begin a demo run |
| POST | `/simulate/step` | `{FeatureRecord, RiskAssessment}` | **the slider** — one step per day |
| POST | `/assess/batch` | RiskAssessment[] | pre-load the whole spiral for smooth scrubbing |
| GET | `/timeline/{user_id}` | EscalationEvent[] | the sponsor view / alert timeline |

---

## 6. Repo layout & stack

```
relapse-radar/
├── web/                # YOU (shell, chart, controls, sponsor view) + P5 (plan, onboarding, glue)
├── shared/
│   ├── contracts.md
│   └── fixtures/       # build against maya_spiral.json + sample_assessment.json
└── docs/
```

| Thing | Choice |
|---|---|
| Stack | **Node 20 · React + Vite + Tailwind** |
| Charts | **Recharts** (line / risk viz) |
| Naming | JSON keys are `snake_case` (from the API); React props your call |
| Commits | prefix `web:` |
| Run | `npm run dev` (from `web/`) |

**You share `web/` with P5** — agree on component boundaries early. Rough split: **you** = demo screen (shell, chart, controls, sponsor view); **P5** = plan/onboarding editor + integration glue + polish. Keep components modular so you don't collide.

---

## 7. How you fit in the build order

```
contracts → (brain + api in parallel) → web wiring → demo
```

You're one of the **two longest poles** (with P1) — start hour one against fixtures, because UI polish takes the most wall-clock time. At Phase-2 integration, P5 helps wire your fixture reads to P3's live API. The critical path is: **contracts → P1 model → P3 API → P4 web → demo**, so the sooner your UI is solid on fixtures, the less risk at the end.

**Coordination:** pair with **P5** (shared `web/`). P5 runs the integration pass that swaps your fixtures for live fetches.

---

## 8. Paste this into your coding agent to start

> I'm building the **P4** slice of **Relapse Radar**, a privacy-first early-warning app for addiction recovery. I own the live-demo screen in `web/` (React + Vite + Tailwind + Recharts). My job: (1) a **phone-styled shell** that looks like a real app on a projector; (2) the **"your line" chart** — value vs the personal normal band, with a risk line climbing across days; (3) a **GREEN/AMBER/RED** indicator + a contributing-signals readout driven by `RiskAssessment.drivers`; (4) **demo controls** — an advance-day slider, an on-device toggle, and a personal-vs-population toggle; (5) a **sponsor companion view** (second-phone screen) showing the alert.
> Build the entire UI against `shared/fixtures/maya_spiral.json` (FeatureRecord[]) and `shared/fixtures/sample_assessment.json` (RiskAssessment) — the slider just indexes into the array; no API needed yet. Honor the JSON contracts in `shared/contracts.md` **exactly**; at integration I'll swap fixture reads for live calls to `/simulate/step`, `/assess/batch`, and `/timeline/{user_id}` (identical shapes). Tone is strengths-based and calm — it's "your line," never a shaming "relapse score." Build only my slice; coordinate component boundaries with P5 who shares `web/`. Never change a shared schema without flagging it. Make it big and legible from the back of a room. `web/` is currently empty (just a README): coordinate with P5 so **exactly one of us** scaffolds the Vite + React + Tailwind app and commits it before either of us builds. The demo slider streams `maya_healthy.json` then `maya_spiral.json` concatenated (days 60→70) — there is no single combined fixture — and I always read `state`/`risk`/`changepoint.started_day` from each RiskAssessment, never hardcoding (the sample says 67 but the data starts day 64). At integration the API is at `http://localhost:8000` with CORS enabled by P3.

---

## 9. Gotchas — read before you build ⚠️

- **`web/` is just a README — there is no app yet.** Before `npm run dev` works, the Vite + React + Tailwind project must be scaffolded. **Coordinate with P5: exactly ONE of you runs `npm create vite@latest` + adds Tailwind, commits it, then you both build inside it.** If you both scaffold, you collide.
- **Your demo data stream = `maya_healthy.json` + `maya_spiral.json` concatenated** (days 60→70, healthy first). There is **no** single combined fixture. `sample_assessment.json` is one example assessment, not the per-day series — don't drive the slider from it.
- **Read everything from each RiskAssessment dynamically — never hardcode.** The sample shows `started_day: 67`, but the spiral data starts at **day 64**; if you hardcode, the climbing line and the "started N days ago" marker won't line up. Whatever the assessment says is what you render.
- **At integration the API is at `http://localhost:8000`** with CORS enabled by P3. If a `fetch` fails with a CORS error, that's P3's middleware to fix, not your bug.

---

## 10. Working agreement

- Contracts are **frozen** — flag before changing.
- **Mock from `shared/fixtures/`**, integrate early, **freeze before polishing**.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- The demo's emotional arc is the product — protect the timing of the SMS moment; it's the punchline.
