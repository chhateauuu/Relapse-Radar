# api/ + llm/ — the backend (P3)

**You own:** the FastAPI server, the deterministic catch-plan rules engine, Twilio (the real SMS — the demo's big moment), and the LLM layer (`../llm/`).

- `main.py` — endpoints per `../shared/contracts.md`. Imports `brain.assess` (falls back to a stub until P1 ships).
- **Rules engine** — read the CatchPlan, apply thresholds + geofence + sustained-days -> decide `self_nudge` vs `notify_circle`. Deterministic on purpose.
- **Twilio** — `/escalate` sends the user's pre-written message. Put creds in `.env` (never commit).
- **LLM** — `../llm/llm.py`: `explain()` + `checkin()`.

Run from repo root: `uvicorn api.main:app --reload` then open http://127.0.0.1:8000/docs
