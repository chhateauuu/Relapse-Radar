"""Simulator sessions for the live demo.   [P3 serving P2]

`/simulate/start` loads a scenario's FeatureRecords; `/simulate/step` advances
one day, runs the brain's `assess`, fills the LLM explanation, records the day
in history, and auto-evaluates the catch-plan rules. The frontend slider just
calls `step` repeatedly and watches the line climb.

Scenarios (source = ../shared/fixtures, the frozen demo arc):
  - "healthy"           : maya_healthy.json
  - "spiral"            : maya_spiral.json
  - "healthy_to_spiral" : healthy then spiral (default, the full money-shot arc)

P2 swap: once the simulator is tuned, a "synthetic" scenario streams
`simulator.run(...)` instead of fixtures — same FeatureRecord shape.
"""
from __future__ import annotations

from typing import Any

from . import store

DEFAULT_SCENARIO = "healthy_to_spiral"


def _scenario_records(scenario: str) -> list[dict[str, Any]]:
    if scenario == "healthy":
        return list(store.load_fixture("maya_healthy.json"))
    if scenario == "spiral":
        return list(store.load_fixture("maya_spiral.json"))
    if scenario in ("healthy_to_spiral", "full", "default"):
        return list(store.load_fixture("maya_healthy.json")) + list(
            store.load_fixture("maya_spiral.json")
        )
    if scenario == "synthetic":
        # Optional P2 path: stream the tuned simulator instead of fixtures.
        try:
            from simulator.simulator import run

            return list(run())
        except Exception:
            return list(store.load_fixture("maya_healthy.json")) + list(
                store.load_fixture("maya_spiral.json")
            )
    raise ValueError(f"unknown scenario: {scenario!r}")


def start(user_id: str, scenario: str | None) -> dict[str, Any]:
    scenario = scenario or DEFAULT_SCENARIO
    records = _scenario_records(scenario)
    store.set_session(user_id, scenario, records)
    store.reset_history(user_id)
    return {"ok": True, "user_id": user_id, "scenario": scenario, "days": len(records)}
