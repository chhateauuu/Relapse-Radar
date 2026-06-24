"""LLM layer — turn model output into human language.   [P3]

The empathy/interface layer (NOT the predictor — that's the brain). Two jobs:
  - explain(assessment) -> a kind, non-clinical sentence from the top drivers
  - checkin()           -> a short HALT-style (Hungry/Angry/Lonely/Tired) nudge

With OPENAI_API_KEY set it calls a real model; otherwise it composes a solid
sentence locally from the drivers so the demo works fully offline. On-device
Ollama is the privacy-story prod path.
"""
from __future__ import annotations

import os
from typing import Any

# Human phrasing for each signal, keyed by (feature, direction).
_PHRASES: dict[tuple[str, str], str] = {
    ("sleep_hours", "down"): "slept less than usual",
    ("late_night_min", "up"): "been on your phone late into the night",
    ("screen_time_min", "up"): "spent more time on your phone",
    ("unlocks", "up"): "been checking your phone restlessly",
    ("outgoing_msgs", "down"): "gone quieter with people",
    ("unique_contacts", "down"): "been reaching out to fewer people",
    ("location_entropy", "down"): "stayed closer to one place",
    ("time_at_home_pct", "up"): "spent more time at home",
    ("dwell_flagged_min", "up"): "spent time somewhere you flagged",
    ("steps", "down"): "moved around less",
}


def _phrase(driver: dict[str, Any]) -> str:
    feature = driver.get("feature", "")
    direction = driver.get("direction", "")
    return _PHRASES.get((feature, direction), feature.replace("_", " "))


def _local_explain(assessment: dict[str, Any]) -> str:
    """Compose a sentence from the top drivers without any external call."""
    drivers = assessment.get("drivers", [])
    if not drivers or assessment.get("state") == "GREEN":
        return "Your line looks steady today."

    top = sorted(drivers, key=lambda d: abs(d.get("z", 0)), reverse=True)[:3]
    parts = [_phrase(d) for d in top]
    if len(parts) == 1:
        body = parts[0]
    elif len(parts) == 2:
        body = f"{parts[0]} and {parts[1]}"
    else:
        body = f"{parts[0]}, {parts[1]}, and {parts[2]}"
    return f"You've {body} the last few days — that pattern has been a rough sign before."


def _openai_explain(assessment: dict[str, Any]) -> str | None:
    """Best-effort real LLM call. Returns None on any failure so callers fall back."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI

        drivers = ", ".join(
            f"{d.get('feature')} ({d.get('direction')}, z={d.get('z')})"
            for d in assessment.get("drivers", [])
        )
        prompt = (
            "You are a warm, non-clinical recovery companion. In ONE short, kind "
            "sentence (no diagnosis, no numbers, second person), reflect back this "
            f"person's recent behavioral drift. Signals: {drivers}."
        )
        resp = OpenAI().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def explain(assessment: dict[str, Any]) -> str:
    """RiskAssessment.drivers -> a kind, non-clinical sentence."""
    if assessment.get("state") == "GREEN" or not assessment.get("drivers"):
        return "Your line looks steady today."
    return _openai_explain(assessment) or _local_explain(assessment)


def checkin() -> str:
    """A short, motivational-interviewing style HALT check-in."""
    return (
        "Hey — I'm noticing your line's been off. Quick HALT check: are you "
        "hungry, angry, lonely, or tired right now?"
    )


if __name__ == "__main__":
    import json
    from pathlib import Path

    a = json.loads(
        (Path(__file__).resolve().parent.parent / "shared" / "fixtures" / "sample_assessment.json").read_text(encoding="utf-8")
    )
    print("explain:", explain(a))
    print("checkin:", checkin())
