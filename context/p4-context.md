# Relapse Radar — P4 Context

**Lane: Frontend — the live-demo screen.** You own `web/` (the shell, the "your line" chart, the demo controls, the sponsor view).

> **Your one job:** build the screen the judges watch. Slide the spiral forward → the **model scores each day** → the line climbs → the state flips GREEN→AMBER→RED → the sponsor's phone lights up, while a live **Backend AI Model** panel shows the model think. This is the emotional money shot.

This file is **self-contained**: you (and your coding agent) should be able to build your whole slice from just this file. Full team doc lives at `docs/Relapse-Radar-Context.md` if you want the deep background.

---

## 1. What we're building (the 90-second version)

Relapse Radar is a **privacy-first, on-device early-warning app for people in addiction recovery.** It learns *your* normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan *you wrote while you were well* — reaches out through the **one person you chose to catch you** (your sponsor), with words you wrote yourself.

**One-liner:** *catches you in your worst moment, through the person you trust, using a plan you wrote in your best moment.*

Why it can win: the flagship attempt (Mindstrong, ~$160M) died because it sent alerts to overloaded **clinicians**, felt like surveillance, and targeted a vague "everyone." Recovery fixes all three — the **sponsor** is a ready-made opted-in catcher, self-monitoring is native to recovery, and **relapse is a literal event** with a steep 90-day high-risk cliff.

**The tone matters in your UI:** strengths-based, **no shaming.** It's not a judgmental "relapse score" — it's *"your line."* Calm, warm, "you're on track" by default. The design principle: always nudge *you* first; never surveillance.

---

## 2. The demo you're building (the money shot) — AS BUILT

**Three panels side by side**, plus a slider labeled **"advance days":**
**Maya's phone** · **her sponsor's phone** · **the Backend AI Model monitor.**

The whole arc is driven by the **real backend model** (FastAPI wrapping `brain.assess`) when it's running, with an offline fallback engine that emits identical shapes so the demo never breaks.

1. **Green state.** Maya, ~60 days sober. "Your line" sits steady inside her normal band; the on-device indicator is lit.
2. **Slide forward.** Each day's `FeatureRecord` is scored by the model. The line climbs; around **day 64–65 it goes AMBER** and an **iOS-style notification** drops onto Maya's phone ("Your line's off").
3. **It explains itself** in plain words (drivers → a kind, non-clinical sentence).
4. **Day 66 → RED.** With `sustained_days = 1`, the deterministic catch-plan fires **the same day she goes red**.
5. **The sponsor's phone lights up** with the message Maya pre-wrote: *"If you get this, I'm having a hard night near somewhere risky — please call me."*
6. **The Backend AI Model monitor** streams the model's work each day: the `POST /assess` call, z-scores vs her baseline, `fusion → risk`, the change-point, `state =`, and on day 66 the `notify_circle → SMS dispatched` line. A live dot shows whether it's talking to the real API.
7. **Punchline:** *"Nothing left her phone but one text she wrote to herself."*

**Auto-play pauses** at the key beats — the line first goes AMBER, then the RED day the sponsor is reached. Pressing play after the end restarts the run.

**Two proof toggles:**
- **Personal vs Population** — population uses generic averages and under-reacts (misses Maya); personal catches it.
- **On-device** — raw data never transmits; only the risk state + her message.

---

## 3. Your slice — AS BUILT ✅

All under `web/src/components/demo/` + `web/src/lib/`:

1. **Phone shell** — `ui/PhoneFrame.jsx` (status bar, notch), big/legible for a projector.
2. **"Your line" chart** — `demo/YourLineChart.jsx` (Recharts): the risk line climbing across days, GREEN/AMBER/RED zone bands (thresholds **0.30 / 0.60**, matching the model), and a "drift began" change-point marker.
3. **State + drivers** — `demo/StateIndicator.jsx` + `demo/SignalReadout.jsx`, driven by `RiskAssessment.state` / `.drivers`.
4. **iOS notification** — `demo/IOSNotification.jsx`, drops in on the AMBER state.
5. **Check-in** — `demo/CheckInChat.jsx` (HALT-style nudge).
6. **Sponsor view** — `demo/SponsorPhone.jsx` (calm until the plan fires, then the alert + Maya's pre-written message + a Call button).
7. **Backend AI Model monitor** — `demo/ModelMonitor.jsx`: a desktop-monitor panel visualizing the model processing each day (pipeline strip, risk gauge, streaming z-score → fusion → state log, escalation line, live/offline indicator).
8. **Demo controls** — `demo/DemoControls.jsx`: advance-day slider, play/pause with **milestone pauses + restart**, on-device toggle, personal-vs-population toggle.
9. **Orchestration + data** — `demo/DemoView.jsx`, `lib/demoData.js` (concatenated fixtures), `lib/assess.js` (offline engine + state/changepoint/timeline helpers), `lib/demoApi.js` (calls the live model, falls back offline).

The **"My plan" tab** (mostly P5) opens to a **prefilled onboarding wizard** matching the demo data; the location step is optional with a real **Leaflet/OpenStreetMap** map (`ui/MiniMap.jsx`).

**Done:** the full demo runs from the slider, driven by the live model, and looks clean on a projector — the line climbs, the state flips, the sponsor screen lights up, and the model panel shows the work.

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

## 5. The API — WIRED ✅

The backend (FastAPI wrapping the model) runs at **`http://127.0.0.1:8000`** (CORS open). The demo uses:

| Method | Path | Used for |
|---|---|---|
| POST | `/assess/batch` | the whole stream → `RiskAssessment[]` (the model's per-day risk / state / drivers) — **primary path** |
| GET | `/` | health (drives the live/offline indicator) |

The frontend points at the API via `web/.env` → `VITE_API_BASE=http://127.0.0.1:8000` (explicit `127.0.0.1` avoids the Windows `localhost`→IPv6 issue). If the API is unreachable, `lib/demoApi.js` transparently falls back to the offline engine and the panels show **"offline"**.

The frontend uses the model's **risk + drivers**, then derives **state** (matching the chart bands), the **change-point**, and the **escalation timeline** from the model's risk series — the escalation is a deterministic rule by design (a model never decides to text someone). Other endpoints (`/simulate/*`, `/timeline`, `/escalate`) exist on the backend and can be wired later for a real server-side Twilio send.

---

## 6. Repo layout & stack — AS BUILT

```
relapse-radar/
├── api/                 # P3 — FastAPI backend (running on :8000)
├── brain/               # P1/P2 — the model (brain.assess / scorer)
├── .venv/               # Python 3.12 venv for the backend (gitignored)
├── web/
│   ├── .env             # VITE_API_BASE=http://127.0.0.1:8000
│   └── src/
│       ├── App.jsx                    # "Live demo" / "My plan" tabs
│       ├── components/demo/           # DemoView, MayaPhone, SponsorPhone, ModelMonitor,
│       │                             # YourLineChart, StateIndicator, SignalReadout,
│       │                             # CheckInChat, IOSNotification, DemoControls
│       ├── components/ui/             # PhoneFrame, MiniMap (Leaflet), Button, Field, Toggle…
│       ├── components/onboarding/ + plan/   # P5 — prefilled wizard + plan editor + PlacesEditor
│       └── lib/                       # demoData, assess, demoApi, api, plan, fixtures
└── shared/fixtures/     # maya_healthy.json, maya_spiral.json, sample_plan.json, …
```

| Thing | Choice |
|---|---|
| Stack | **Node 20 · React + Vite + Tailwind v4** |
| Charts | **Recharts** ("your line") |
| Map | **Leaflet + OpenStreetMap** (flagged-places map) |
| Backend | **Python 3.12 venv · FastAPI · uvicorn** (model = `brain.assess`) |
| Naming | JSON keys `snake_case` (from the API) |
| Commits | prefix `web:` |

**Run it:**
- **Backend** (repo root): `.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`
- **Frontend** (`web/`): `npm run dev` → http://localhost:5174/
- Node + Python were installed via winget; **new** terminals have them on PATH.

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

## 9. Gotchas (current) ⚠️

- **Use `127.0.0.1`, not `localhost`, for the API** (pinned in `web/.env`). On Windows `localhost` can resolve to IPv6 `::1` while uvicorn binds IPv4 → fetches fail.
- **The backend must be running** for the live model + the monitor's "live" dot. If it's down, everything still works via the offline engine (panels show "offline").
- **Read everything from each RiskAssessment dynamically — never hardcode days.** The model's arc: GREEN → AMBER (day 64–65) → RED + SMS (day 66). State thresholds are **0.30 / 0.60** to match the model; `sustained_days = 1` so the sponsor text fires the same day she goes red.
- **`uvicorn[standard]` won't build on this ARM64 box** (needs MSVC); use plain `uvicorn`. The ML libs (lightgbm/shap/ruptures) aren't needed — the scorer is pure-Python and Twilio/LLM are lazily imported.
- **Restarting:** new terminals must refresh PATH or just open fresh; then run the two commands in §6.

---

## 10. Working agreement

- Contracts are **frozen** — flag before changing.
- **Mock from `shared/fixtures/`**, integrate early, **freeze before polishing**.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- The demo's emotional arc is the product — protect the timing of the SMS moment; it's the punchline.
