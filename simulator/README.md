# simulator/ — the demo engine (P2)

Generates a synthetic user: a stable **healthy baseline**, then an **injectable relapse spiral** (sleep down, comms down, mobility collapsing, drifting to a flagged place). Emits FeatureRecords per `../shared/contracts.md` and is what the live demo slider steps through.

- `simulator.py` — baseline + spiral generators + `run()` stream.
- **Also write `../shared/fixtures/`** from here so the whole team mocks against realistic data. Build this **first** — it unblocks P3/P4/P5.

Run: `python simulator/simulator.py`
