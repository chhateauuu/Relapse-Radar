# web/ — the phone UI (P4 + P5)

React + Vite + Tailwind, styled as a phone (must look real on a projector). Talks to the API (`../api/`) — mock against `../shared/fixtures/` until it's up.

## Split (so you two don't collide)
**P4 — the demo screen:**
- the phone shell
- the **"your line"** chart (value vs personal normal band, risk climbing) — Recharts
- the GREEN/AMBER/RED state + the "behind-the-glass" live signal readout
- the demo controls — advance-day slider, on-device toggle, personal-vs-population toggle
- the **sponsor companion view** (the second-phone screen)

**P5 — plan + glue + polish:**
- the geofence + **catch-plan editor** + onboarding ("mark risky places, choose your person, write your message")
- wire `web -> api -> llm` as each comes online
- the whole-app visual polish pass + demo dry-runs

## Setup (P4 to scaffold)
```bash
npm create vite@latest . -- --template react
npm install
npm install recharts
npm run dev
```
Honor `../shared/contracts.md` exactly.
