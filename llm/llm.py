"""LLM layer — turn model output into human language.   [P3]

The empathy/interface layer (NOT the predictor — that's the brain). Stubs return
canned text so the demo works without an API key. Swap in a real call
(OpenAI/Anthropic; on-device Ollama is the privacy-story prod path).
"""
from __future__ import annotations

from typing import Any


def explain(assessment: dict[str, Any]) -> str:
    """RiskAssessment.drivers -> a kind, non-clinical sentence."""
    drivers = assessment.get("drivers", [])
    if not drivers or assessment.get("state") == "GREEN":
        return "Your line looks steady today."
    # TODO(P3): real prompt over the top drivers (sleep/comms/location/...).
    return (
        "You've slept less, gone quieter with people, and spent time somewhere "
        "you flagged the last few days — that pattern has been a rough sign before."
    )


def checkin() -> str:
    """A short, motivational-interviewing style HALT check-in."""
    return "Hey — I'm noticing your line's been off. HALT check: hungry, angry, lonely, or tired?"


if __name__ == "__main__":
    import json
    from pathlib import Path

    a = json.loads((Path(__file__).resolve().parent.parent / "shared" / "fixtures" / "sample_assessment.json").read_text(encoding="utf-8"))
    print("explain:", explain(a))
    print("checkin:", checkin())
