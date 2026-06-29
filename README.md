# Relapse Radar

Privacy-first early-warning app for people in addiction recovery. It learns your normal phone-behavior rhythm, catches a relapse spiral days early, and — using a plan you wrote while well — reaches out through the person you chose to catch you.


## Repo layout
| Folder | What lives here |
|---|---|---|
| `brain/` | ML: baseline, model, AUC, change-point, SHAP, ablation, `assess()` |
| `simulator/` | synthetic healthy baseline + injectable relapse spiral |
| `api/` | FastAPI + catch-plan rules engine + Twilio |
| `llm/` | explanation + HALT check-in |
| `web/` | phone UI (demo screen + plan/onboarding) |
| `shared/` | **frozen** contracts + sample fixtures (source of truth) |
