# Relapse Radar

Privacy-first early-warning app for people in addiction recovery. It learns your normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan you wrote while well — reaches out through the person you chose to catch you.

**Full context, pitch, architecture, and per-person build spec:** [`docs/Relapse-Radar-Context.md`](docs/Relapse-Radar-Context.md)

## Repo layout
| Folder | Owner | What lives here |
|---|---|---|
| `brain/` | P1 + P2 | ML: baseline, model, AUC, change-point, SHAP, ablation, `assess()` |
| `simulator/` | P2 | synthetic healthy baseline + injectable relapse spiral |
| `api/` | P3 | FastAPI + catch-plan rules engine + Twilio |
| `llm/` | P3 | explanation + HALT check-in |
| `web/` | P4 + P5 | phone UI (demo screen + plan/onboarding) |
| `shared/` | P5 stewards | **frozen** contracts + sample fixtures (source of truth) |
| `deck/` | team | demo, slides, ethics, backup video (shared final lap) |
| `docs/` | — | the context doc |

## The 5-person split
- **P1 — Brain: data + models** — loaders, personal baseline, LightGBM, AUC, `assess()`.
- **P2 — Brain: detection + proof + simulator** — change-point/state, SHAP drivers, ablation chart, simulator.
- **P3 — Backend** — FastAPI, rules engine, Twilio (the real SMS), LLM explain/check-in.
- **P4 — Frontend: demo screen** — phone UI, "your line" chart, controls, sponsor view.
- **P5 — Frontend: plan + glue** — plan/onboarding editor, `/shared`, integration, polish.

## Start here
1. Read [`docs/Relapse-Radar-Context.md`](docs/Relapse-Radar-Context.md) — Part 1 (the why/what) + your own §B6 slice.
2. Honor the JSON contracts in [`shared/contracts.md`](shared/contracts.md) **exactly**.
3. Mock your dependencies from [`shared/fixtures/`](shared/fixtures/).
4. Run locally:
   - brain: `python -m brain.train`
   - api: `uvicorn api.main:app --reload`
   - web: `npm run dev`

## How we work
Contract gate first (lock `shared/`) → everyone builds in parallel against fixtures → integrate brain → api → web → polish + demo. See §B8 in the context doc.
