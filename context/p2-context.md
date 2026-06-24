# Relapse Radar — P2 Context

**Lane: Brain — detection, proof & simulator.** You own `brain/eval/` and `simulator/`.

> **Your one job:** prove the model is real (change-point state + SHAP drivers + the personal-vs-population ablation chart) and build the **simulator** that drives the live demo and writes everyone's fixtures.

This file is **self-contained**: you (and your coding agent) should be able to build your whole slice from just this file. Full team doc lives at `docs/Relapse-Radar-Context.md` if you want the deep background.

---

## 1. What we're building (the 90-second version)

Relapse Radar is a **privacy-first, on-device early-warning app for people in addiction recovery.** It learns *your* normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan *you wrote while you were well* — reaches out through the **one person you chose to catch you** (your sponsor), with words you wrote yourself.

**One-liner:** *catches you in your worst moment, through the person you trust, using a plan you wrote in your best moment.*

Why it can win: the flagship attempt (Mindstrong, ~$160M) died because it sent alerts to overloaded **clinicians**, felt like surveillance, and targeted a vague "everyone." Recovery fixes all three — the **sponsor** is a ready-made opted-in catcher, self-monitoring is native to recovery, and **relapse is a literal event** with a steep 90-day high-risk cliff.

**The three layers — know which one is yours:**

| Layer | What it is | Real AI? | Owner |
|---|---|---|---|
| Escalation / geofence / thresholds | "if RED for 2 days AND near a flagged place → text sponsor" | No — deterministic *by design* | P3 |
| **The "is your line off?" engine** | detect that *you* deviated from *your own* normal, score risk, find the change-point | **Yes — the real ML** | **P1 + P2** |
| The empathic interface | explain the risk in plain words, run the check-in | Generative AI (interface only) | P3 |

**You and P1 own the crown jewel** — the brain. P1 builds the data loaders + personal baseline + LightGBM + `assess()`; **you** build the change-point/state detector, the SHAP drivers, the ablation proof chart, and the simulator. Clean file split keeps you out of each other's way.

---

## 2. Your slice (what done looks like)

You build, end to end:

1. **Feature-engineering helpers** (`brain/eval/` or shared with P1's loader) — location entropy, sleep proxy, late-night minutes, comms-drop. Agree with P1 on where these live so you don't duplicate.
2. **The change-point / state detector** (`brain/eval/`) — over the risk series (or feature series), decide **`state`** (`GREEN | AMBER | RED`) and **`changepoint.started_day`**. Use **`ruptures`** (PELT/CUSUM-style). The whole point: distinguish **one bad night** from a **sustained multi-day drift** — that's what stops the app spamming false alarms. Expose something like `detect(risk_series) -> {state, changepoint}` that P1's `assess.py` can call.
3. **SHAP drivers** (`brain/eval/`) — run `shap` over P1's trained model for a given record → the **`drivers`** list (top features, each with a signed `z` and `direction`). This both feeds `RiskAssessment.drivers` and the LLM explanation. Expose `drivers(model, record) -> [...]`.
4. **The personal-vs-population ablation chart** (`brain/notebooks/`) — **the money proof.** Train/score two ways: (a) personal baseline (per-user z-scores) vs (b) a single population threshold. Show personal **beats** population (higher AUC / catches Maya, fewer false alarms). This one chart is the difference between "real individualized AI" and "if-statement with a GPT wrapper."
5. **The simulator** (`simulator/`) — synthetic healthy baseline + **injectable relapse spiral**, emitting a `FeatureRecord` stream. It drives the live demo (the front-end slider steps through these days) **and** writes `shared/fixtures/` so the whole team can mock against realistic data. *A working skeleton already exists in `simulator/simulator.py` — your job is to tune the day-by-day curves so the spiral feels real, and wire `step()`/fixture-writing.*

**Done when:**
- The **ablation chart** shows personal > population.
- `detect()` and `drivers()` exist and are callable from P1's `assess()`.
- `simulator` produces a clean **healthy → spiral** run and (re)writes the fixtures.

**Start immediately (no dependencies — and this UNBLOCKS THE WHOLE TEAM):** the **simulator + fixtures.** Everyone (P3 API, P4/P5 web) mocks against `shared/fixtures/maya_healthy.json` and `maya_spiral.json` — so the sooner those are realistic, the sooner everyone's demo looks real. Then build change-point on a synthetic risk series.

**You wait for:** P1's trained model — but only for SHAP `drivers` and the ablation. Use a synthetic risk series until P1 ships, then swap in the real model.

---

## 3. The FROZEN contracts — honor these EXACTLY ⭐

Every slice codes against these shapes. **Do not change a schema without flagging the team.** Canonical copy: `shared/contracts.md`. You and P5 are the **stewards of `shared/`**, so you especially must keep fixtures matching these shapes exactly.

**FeatureRecord** — one user-day of signals (what your simulator EMITS, one per day):
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
For fixtures: `label` `0` on healthy days, `1` on spiral days.

**RiskAssessment** — output of `assess()`. **You fill `state`, `drivers`, `changepoint`** (P1 fills `risk`; P3's LLM fills `explanation`):
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
`state` ∈ `GREEN | AMBER | RED`. `direction` ∈ `up | down`. `z` is the signed z-score vs the user's own normal.

> CatchPlan + EscalationEvent + the API endpoints are in `shared/contracts.md` — they're P3/P5's surface, but as a `shared/` steward keep an eye on them.

---

## 4. Repo layout (your corner)

```
relapse-radar/
├── brain/
│   ├── data/           #   P1 — dataset loaders
│   ├── models/         #   P1 — saved model + baseline
│   ├── train.py        #   P1 — trains + AUC
│   ├── assess.py       #   P1 — assess(); CALLS your eval/ module
│   ├── eval/           #   YOU — change-point (ruptures), SHAP drivers, ablation
│   └── notebooks/      #   P1/P2 — AUC + the ablation chart
├── simulator/          #   YOU — simulator.py (healthy + injectable spiral)
├── shared/             #   YOU + P5 steward this
│   ├── contracts.md
│   └── fixtures/       #   YOU write these from the simulator
└── docs/
```

**File split with P1 (avoid collisions):** P1 owns `models/`, `train.py`, `assess.py`. You own `eval/` and `simulator/`. `assess.py` imports your `eval/` functions — **agree on the signatures on day one** (e.g. `detect(risk_series) -> {state, changepoint}`, `drivers(model, record) -> [...]`).

---

## 5. Stack & conventions

| Thing | Choice |
|---|---|
| Language | **Python 3.11** |
| Your libs | pandas · numpy · **ruptures** (change-point) · **shap** · matplotlib (ablation chart) · (LightGBM model comes from P1) |
| Naming | JSON keys + Python both `snake_case`, canonical |
| Per folder | a README + one run command |
| Commits | prefix by area: `brain:` |
| Run | `python -m simulator.simulator` (stream records) · ablation/eval via `brain/notebooks/` |

Install: `pip install -r requirements.txt` from repo root.

---

## 6. How you fit in the build order

```
Phase 0 contract gate → Phase 1 everyone parallel on mocks → Phase 2 integrate brain→api→web
```

- **You + P5 run the Phase-0 contract gate:** produce/confirm `shared/contracts.md` + the four fixtures (`maya_healthy.json`, `maya_spiral.json`, `sample_assessment.json`, `sample_plan.json`). **This one step unblocks all five people** — do it first, before feature code.
- **Phase 1:** build the simulator (unblocks everyone), then change-point on a synthetic risk series. Mock P1's model for `drivers`/ablation.
- **Phase 2:** swap synthetic risk for P1's real model → finish SHAP drivers + the real ablation. Your simulator feeds P3's `/simulate/start` and `/simulate/step` endpoints, which feed P4's slider.

**Coordination:** pair tightly with **P1** (shared `brain/`). Sit next to P5 for the `shared/` stewardship.

---

## 7. Paste this into your coding agent to start

> I'm building the **P2** slice of **Relapse Radar**, a privacy-first early-warning app for addiction recovery. I own `brain/eval/` and `simulator/`. My job: (1) a **simulator** that emits a `FeatureRecord` stream — a synthetic healthy baseline plus an injectable multi-day relapse spiral — and writes realistic fixtures to `shared/fixtures/`; (2) a **change-point / state detector** using `ruptures` over the risk series that outputs `state` (GREEN/AMBER/RED) and `changepoint.started_day`, distinguishing one bad night from sustained drift; (3) **SHAP** drivers over P1's model → the `drivers` list; (4) the **personal-vs-population ablation** chart proving the personal baseline beats a population threshold.
> Honor the JSON contracts in `shared/contracts.md` **exactly** (I fill `state`/`drivers`/`changepoint` in RiskAssessment; my simulator emits FeatureRecords). Expose `detect()` and `drivers()` so P1's `brain/assess.py` can call them. Mock P1's trained model with a synthetic risk series until it exists. Build only my slice. Never change a shared schema without flagging it. The simulator's spiral curves are the heart of the demo — tune them so sleep drops, late-night spikes, comms thin out, mobility shrinks, and time near a flagged place climbs over the spiral days. The four fixtures in `shared/fixtures/` already exist and match the contract — if I regenerate them, keep the exact shapes, keep healthy/spiral self-consistent, and coordinate with P5 first; and `changepoint.started_day` must be computed by my detector, never hardcoded.

---

## 8. Gotchas — read before you build ⚠️

- **The four fixtures ALREADY EXIST and already match the contract** — `maya_healthy.json` (days 60–63, `label 0`), `maya_spiral.json` (days 64–70, `label 1`), plus `sample_assessment.json` and `sample_plan.json`. If your simulator rewrites them, **keep the exact shape and keep healthy/spiral self-consistent**, and **coordinate with P5** (co-steward of `shared/`) before overwriting — P1/P3/P4 all mock against them.
- **`changepoint.started_day` comes from your detector, never a hardcoded constant.** `sample_assessment.json` shows `67`, but `maya_spiral.json` visibly degrades from **day 64** — compute the real onset so the demo timeline is coherent. A hardcoded `67` is the one thing that makes the on-screen "started N days ago" marker wrong.
- **Agree the `detect()` / `drivers()` signatures with P1 on day one** — `assess.py` imports and calls them.
- **Run Python from the repo root** (`python -m simulator.simulator`) so paths resolve.

---

## 9. Working agreement

- Contracts are **frozen** — flag before changing. You're a `shared/` steward, so guard them.
- **Mock your dependencies**, integrate early, **freeze before polishing**.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- The ablation chart is the single most important proof artifact in the whole project — make it clean and legible on a projector.

---

## 10. Progress log — what's built so far (updated 6/24)

**Status: P2's independent scope is DONE and committed. Everything remaining is gated on P1.**

### Built + committed
| File | What it does | Verified |
|---|---|---|
| `brain/eval/detect.py` | change-point + GREEN/AMBER/RED state. ruptures PELT with a dependency-free CUSUM fallback. Fills `changepoint.started_day`. | smoke test: `RED`, drift onset ~day 65 |
| `brain/eval/drivers.py` | top-3 z-score drivers in contract shape. SHAP-ready (swap `_z` for TreeExplainer when P1's model lands). | smoke test: `late_night_min`, `unlocks`, `sleep_hours` |
| `brain/eval/__init__.py` | exports `detect`, `drivers`, `state_for` → P1 does `from brain.eval import detect, drivers` | — |
| `simulator/simulator.py` | tuned: **reproducible (seeded)**, accelerating spiral, integer-clamped counts. `run()` signature unchanged so P3's `/simulate` still imports it. New: `series()` helper, `SPIRAL_TARGET`, `start_day`/`seed` args. | clean healthy(60–63)→spiral(64–70) arc |
| `brain/eval/ablation.py` + `ablation.png` | **the proof chart.** Synthetic 80-user cohort, honest GroupKFold-by-user AUC. | **population (raw) 0.654 vs personal (per-user z) 0.892, +0.238 lift** |

**Commits:** `d8786d3` (detector + tuned simulator), `fce4898` (ablation + chart). Context briefings: `c3d4c69`.

### Environment (this machine)
- No system Python existed — installed **Python 3.11.9** at `%LOCALAPPDATA%\Programs\Python\Python311\python.exe` (not on PATH; use the full path or prepend it). All `requirements.txt` deps installed (numpy, ruptures, shap, lightgbm, scikit-learn, matplotlib, fastapi…).
- **Run from the repo root:** `python -m brain.eval.detect` · `python -m brain.eval.drivers` · `python -m brain.eval.ablation` (writes `ablation.png`).

### Remaining — all blocked on P1
- **Wire `detect`/`drivers` into `brain/assess.py`** — P1 owns `assess.py` and produces `risk`. Until then the live API line is flat-GREEN unless run with `USE_MOCK_BRAIN=1`.
- **Swap drivers z-scores → SHAP `TreeExplainer`** — needs P1's trained LightGBM object.
- **Real-data ablation panel** — needs P1's model + a shared `to_zscores(record, history)` function so model input + drivers + ablation all use the *same* per-user baseline.

### Notes for the team
- P1 (Siam) is shipping **LightGBM** (StudentLife honest AUC ~0.545 ≈ near chance, because StudentLife is daily-affect not relapse). Plan: pull the headline AUC from **CrossCheck** (real relapse labels) **or** lead with this ablation as the proof and call StudentLife the method-check.
- The ablation is **synthetic + honestly labeled** — it proves the *mechanism* (personal baselining is the lever, +0.238 AUC). The real-data panel on P1's model is the honest validation, still pending.
