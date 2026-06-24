# Relapse Radar — P1 Context

**Lane: Brain — data + models.** You own `brain/data/`, `brain/models/`, `brain/train.py`, and `brain/assess.py`.

> **Your one job:** turn real public behavioral data into a trained model that learns each person's *own* normal and outputs a relapse-risk score — and ship the `assess()` function every other slice imports.

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

**You and P2 own the crown jewel** — the brain. You build the model + baseline + risk score + `assess()`; P2 builds the change-point/state detector, the SHAP drivers, the ablation chart, and the simulator. Clean file split (below) keeps you out of each other's way.

---

## 2. Your slice (what done looks like)

You build, end to end:

1. **Dataset loaders** (`brain/data/`) — pull a public dataset into a tidy per-user-day `FeatureRecord` table.
   - **StudentLife first** — open download, no gate, easiest. ~48 users, 10 weeks, phone sensing, PHQ-9 depression labels.
   - Then **GLOBEM** (PhysioNet, credentialed; 497 users, 700+ person-years, has a GitHub benchmark with feature-extraction code) and/or **CrossCheck** (Dartmouth/UW; ~63 patients with **actual psychotic-relapse labels** — this is where your real *relapse* AUC comes from).
2. **The personal baseline** (`brain/models/`) — per **user + feature** rolling expected value + spread (median / IQR), with weekday-vs-weekend handling → **per-feature z-scores** ("how far is today from *your* normal"). This is the heart of the privacy + accuracy story: deviation from *your own* rhythm predicts better than a population average.
3. **The LightGBM fusion model** — maps the z-score vector → `risk` in [0, 1]. No single signal predicts relapse; it's the *joint* pattern.
4. **`brain/train.py`** — loads data → builds baseline → trains LightGBM → **saves the model** to `brain/models/` → plots **ROC / AUC** to `brain/notebooks/`.
5. **`brain/assess.py`** — the function everyone imports: **`assess(FeatureRecord) -> RiskAssessment`**. You fill `risk`; you call P2's detector module for `state` / `drivers` / `changepoint` (mock those keys until P2 lands — see §6).

**Done when:**
- A saved model + a printed **AUC on real data** (target the literature's **0.70–0.88**).
- `assess()` returns a schema-valid `RiskAssessment` (see contracts below).
- (Stretch, with P2) the **personal-vs-population ablation** shows personal baseline beats a population threshold — that's the money proof that this is real individualized AI, not an if-statement.

**Start immediately (no dependencies — you are the head of the critical path, go first, go fast):** dataset loading + the personal baseline. Everything downstream (P3 API → P4/P5 web) eventually waits on your `assess()`, so an early stub that returns valid JSON (already in `assess.py`) unblocks them while you build the real thing.

**You wait for:** nothing to start. Only P2's `detect()` / `drivers()` for the non-`risk` fields of `RiskAssessment` — mock them until then.

---

## 3. The FROZEN contracts — honor these EXACTLY ⭐

Every slice codes against these shapes. **Do not change a schema without flagging the team** (5 people depend on them matching). Canonical copy: `shared/contracts.md`. Sample instances: `shared/fixtures/`.

**FeatureRecord** — one user-day of signals (this is your model's INPUT row):
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
`label` is `null` in production; `0` (healthy) / `1` (pre-relapse) when training on labeled data.

**RiskAssessment** — output of `assess()` (you fill `risk`; P2 fills `state` / `drivers` / `changepoint`; P3's LLM fills `explanation`):
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
`state` ∈ `GREEN | AMBER | RED`. `risk` ∈ [0, 1].

> The other two contracts (CatchPlan, EscalationEvent) and the API endpoints don't constrain your code directly — they're P3/P5's. They're in `shared/contracts.md` if you're curious.

---

## 4. Repo layout (your corner)

```
relapse-radar/
├── brain/              # P1 + P2 — ML
│   ├── data/           #   P1 — dataset loaders (StudentLife → GLOBEM → CrossCheck)
│   ├── models/         #   P1 — saved model + baseline
│   ├── train.py        #   P1 — trains + emits AUC chart
│   ├── assess.py       #   P1 — assess(FeatureRecord) -> RiskAssessment   <-- the core everyone imports
│   ├── eval/           #   P2 — change-point, SHAP drivers, ablation chart
│   └── notebooks/      #   P1/P2 — AUC + personal-vs-population ablation
├── simulator/          # P2 — synthetic healthy + injectable spiral
├── shared/             # contracts + fixtures = source of truth for schemas
│   ├── contracts.md
│   └── fixtures/       # maya_healthy.json, maya_spiral.json, sample_assessment.json, sample_plan.json
└── docs/               # the full context doc
```

**File split with P2 (avoid collisions):** you own `models/`, `train.py`, `assess.py`. P2 owns `brain/eval/` (change-point, SHAP, ablation) and `simulator/`. `assess.py` *calls into* P2's `eval/` module — agree on that function signature early (e.g. `detect(risk_series) -> {state, changepoint}` and `drivers(model, record) -> [...]`).

---

## 5. Stack & conventions

| Thing | Choice |
|---|---|
| Language | **Python 3.11** |
| Your libs | pandas · numpy · scikit-learn · **lightgbm** · matplotlib (ROC plot). (P2 adds `ruptures` + `shap`.) |
| Naming | JSON keys + Python both `snake_case`, canonical |
| Per folder | a README + one run command |
| Commits | prefix by area: `brain:` for you |
| Run | `python -m brain.train` (train + AUC) · `python -m brain.assess` (smoke-test assess on a fixture) |

Install: `pip install -r requirements.txt` from repo root.

---

## 6. How you fit in the build order

```
contracts (done) → P1 model + assess  →  P3 API  →  P4/P5 web  →  demo
```

You are the **critical path**. Concretely:

1. **Now:** keep the existing `assess.py` stub returning valid JSON (it already does) so P3 can wire `/assess` today. Then start dataset loaders + baseline.
2. **Build real `risk`:** baseline z-scores → LightGBM → `risk`. Mock `state` / `drivers` / `changepoint` with safe defaults until P2's `eval/` module exists, then import it.
3. **At integration (Phase 2):** P3 swaps its mock `assess` for your real `from brain.assess import assess`. Make sure the import is cheap (lazy-load the model file; don't retrain on import).

**Coordination:** pair tightly with **P2** (you share `brain/`). Agree on the `eval/` function signatures on day one so `assess.py` can call them without churn.

---

## 7. Paste this into your coding agent to start

> I'm building the **P1** slice of **Relapse Radar**, a privacy-first early-warning app for addiction recovery. I own `brain/data/`, `brain/models/`, `brain/train.py`, and `brain/assess.py`. My job: dataset loaders (StudentLife first, then GLOBEM/CrossCheck) → a **personal per-user baseline** (rolling median/IQR → per-feature z-scores, weekday/weekend aware) → a **LightGBM** model mapping the z-score vector to a `risk` in [0,1] → `train.py` that saves the model and emits an **ROC/AUC** chart → `assess(FeatureRecord) -> RiskAssessment`.
> Honor the JSON contracts in `shared/contracts.md` **exactly** (FeatureRecord in, RiskAssessment out — I fill `risk`; `state`/`drivers`/`changepoint` come from P2's `brain/eval/` module, which I should call but can mock with safe defaults until it exists). Mock my data dependencies from `shared/fixtures/`. Build only my slice. Never change a shared schema without flagging it. Target a real AUC of 0.70–0.88 on real labeled data, and keep model loading lazy so importing `assess` is cheap. Run every Python command from the repo root so `brain.` imports and `shared/fixtures` paths resolve, and until P2's `brain/eval/` module lands, return the safe defaults already in the `assess.py` stub for `state`/`drivers`/`changepoint` — never omit a contract field.

---

## 8. Gotchas — read before you build ⚠️

- **Run every Python command from the repo root** — `python -m brain.train`, `python -m brain.assess`. Don't `cd brain/` and run files directly, or `brain.` imports and the `shared/fixtures` paths break.
- **Keep `assess()` cheap to import.** Lazy-load the saved model inside the call (or on first use), not at module top — **P3 imports `assess` at API startup**, so a heavy import or a missing model file takes the whole API down. The skeleton's stub already returns valid JSON; keep that path working as a fallback.
- **Never omit a contract field.** Until P2's `brain/eval/` exists, fill `state` / `drivers` / `changepoint` with the stub defaults (`"GREEN"` / `[]` / `{ "active": false, "started_day": null }`). A missing key breaks P3 and P4.
- **Agree the `eval/` signatures with P2 on day one** (e.g. `detect(risk_series) -> {state, changepoint}`, `drivers(model, record) -> [...]`) so `assess.py` wires to them in one line.
- **The fixtures already exist** — `maya_healthy.json` (days 60–63) and `maya_spiral.json` (days 64–70). Smoke-test `assess()` against them; **don't rewrite them** (that's P2/P5).

---

## 9. Working agreement

- Contracts are **frozen** — flag before changing.
- **Mock your dependencies** (use `shared/fixtures/`), integrate early.
- Keep your status row current in `docs/Relapse-Radar-Context.md` §B10.
- The honest framing that wins judges: we validate the *method* on the best available labeled behavioral data (depression/schizophrenia relapse); productionizing for addiction needs a recovery-cohort study — that's on the roadmap, not hidden.

---

## 10. Progress log — agent changes (append-only; pull before you start) ⭐

> Team convention: every agent action on the P1 slice is appended here so cross-person tracking is easy. **Pull before you start.** Newest entry at the bottom.

### 2026-06-24 — P1 (Siam) — model trained + saved, paths made configurable

**Status: P1 functionally complete and integration-ready. `assess()` works, honors the frozen contract, and unblocks P3. LightGBM trained + saved.**

**Code changes**
- `brain/config.py` — `MODELS_DIR` is now configurable via the `RELAPSE_MODELS_DIR` env var and **defaults to `brain/model/`** (singular). Dataset path still overridable via `RELAPSE_DATASET_DIR`.
- `brain/scorer.py` — `_ARTIFACT` now lazy-loads the trained model from `brain/model/` (respects `RELAPSE_MODELS_DIR`) so training output and serving stay in sync.

**Training run (in venv `C:\custom\Hackathon\.venv`, dataset `C:\custom\Hackathon\dataset\studentlife`)**
- Loaded **2439 user-days across 46 users** (8/46 positive, 19% positive user-days).
- Backend: **LightGBM** (`lightgbm.sklearn.LGBMClassifier`) — verified by loading the artifact, not just the log.
- **GroupKFold AUC: 0.561** — near-chance, expected/honest (StudentLife PHQ-9 = trait depression, not relapse). Headline AUC will come from CrossCheck or P2's ablation.
- Artifact saved → **`brain/model/fusion_model.joblib`** (422 KB). ROC chart → `brain/notebooks/roc_auc.png`.

**Serving note (important for P2/P3):** `assess()` serves the **calibrated logistic fallback** by default (smooth GREEN→RED demo arc). The trained LightGBM only loads when `RELAPSE_USE_TRAINED_MODEL=1`, because StudentLife labels would flatten the demo. The trained model exists for inspection/SHAP.

**Run commands**
```powershell
$env:RELAPSE_DATASET_DIR="C:\custom\Hackathon\dataset\studentlife"
& "C:\custom\Hackathon\.venv\Scripts\python.exe" -m brain.train     # train + AUC, saves to brain/model/
& "C:\custom\Hackathon\.venv\Scripts\python.exe" -m brain.assess    # smoke-test on fixtures
```

**Dependency check for P2 (asked 6/24):**
- ✅ UNBLOCKED: `detect`/`drivers` already wired into `assess.py`; trained LightGBM object now available at `brain/model/fusion_model.joblib` for the SHAP `TreeExplainer` swap + real-data ablation.
- ⚠️ STILL OPEN (P1 TODO): a **shared per-user rolling baseline** (`to_zscores(record, history)`, median/IQR, weekday/weekend) so model input + drivers + ablation all z-score identically. Today `scorer.py` only exposes a **population** baseline. A draft exists at `brain/draft_files/brain/models/baseline.py` — not yet promoted into the live `brain/` package. Note: the saved model was trained on **population** z-scores, so SHAP against a personal baseline needs alignment first.
