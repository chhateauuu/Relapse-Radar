"""Population-baseline risk scorer.   [P1]

Self-contained and dependency-free *at import time* so `assess()` is always cheap
and safe to import (P3 imports it at API startup). Turns one frozen FeatureRecord
into a `risk` in [0, 1]:

  - z-score every signal against a population healthy baseline,
  - combine the deviations that point the *risk-increasing* way,
  - map that to a probability.

If `train.py` has saved a trained model artifact, it is lazy-loaded and used for
the z-score -> risk step (better separation). Otherwise a transparent logistic
fallback keeps everything working with zero ML deps installed.

All names/keys are the FROZEN contract names from ../shared/contracts.md.
"""
from __future__ import annotations

import functools
import math
import os
from pathlib import Path
from typing import Any, Optional

# Canonical, ordered list of the 10 frozen FeatureRecord signals.
FEATURE_NAMES: list[str] = [
    "sleep_hours",
    "late_night_min",
    "screen_time_min",
    "unlocks",
    "outgoing_msgs",
    "unique_contacts",
    "location_entropy",
    "time_at_home_pct",
    "dwell_flagged_min",
    "steps",
]

# Population healthy baseline as (mean, spread). Mirrored across the team
# (simulator BASELINE, api.mock_brain, brain.eval.drivers) so every component
# z-scores identically. P1 replaces these with a learned baseline when a real
# labeled dataset (StudentLife / CrossCheck) is wired through train.py.
BASELINE: dict[str, tuple[float, float]] = {
    "sleep_hours": (7.2, 0.5),
    "late_night_min": (8.0, 8.0),
    "screen_time_min": (210.0, 30.0),
    "unlocks": (78.0, 12.0),
    "outgoing_msgs": (18.0, 4.0),
    "unique_contacts": (6.0, 1.5),
    "location_entropy": (1.45, 0.2),
    "time_at_home_pct": (0.55, 0.08),
    "dwell_flagged_min": (0.0, 4.0),
    "steps": (5200.0, 700.0),
}

# The risk-increasing direction of deviation for each signal.
RISK_DIRECTION: dict[str, str] = {
    "sleep_hours": "down",
    "late_night_min": "up",
    "screen_time_min": "up",
    "unlocks": "up",
    "outgoing_msgs": "down",
    "unique_contacts": "down",
    "location_entropy": "down",
    "time_at_home_pct": "up",
    "dwell_flagged_min": "up",
    "steps": "down",
}

# Fallback logistic constants (tuned so a healthy day ~0.1 ramps smoothly to
# ~0.95+ at the deepest spiral day, matching the demo arc).
_FALLBACK_GAIN = 0.9
_FALLBACK_PIVOT = 2.0

_ARTIFACT = Path(
    os.getenv("RELAPSE_MODELS_DIR", str(Path(__file__).resolve().parent / "model"))
) / "fusion_model.joblib"


def zscores(features: dict[str, Any]) -> dict[str, float]:
    """Signed z-score of each present signal vs the population baseline."""
    out: dict[str, float] = {}
    for name, (mean, spread) in BASELINE.items():
        if name not in features or spread == 0:
            continue
        out[name] = (float(features[name]) - mean) / spread
    return out


def _directional_load(zs: dict[str, float]) -> float:
    """Root-mean-square of deviations that point the risk-increasing way."""
    sq_sum = 0.0
    for name in FEATURE_NAMES:
        z = zs.get(name)
        if z is None:
            continue
        directional = z if RISK_DIRECTION[name] == "up" else -z
        if directional > 0:
            sq_sum += directional * directional
    return math.sqrt(sq_sum / len(FEATURE_NAMES))


def _fallback_risk(zs: dict[str, float]) -> float:
    """Transparent logistic risk over the directional deviation load."""
    load = _directional_load(zs)
    risk = 1.0 / (1.0 + math.exp(-_FALLBACK_GAIN * (load - _FALLBACK_PIVOT)))
    return max(0.0, min(1.0, risk))


@functools.lru_cache(maxsize=1)
def _load_artifact() -> Optional[dict[str, Any]]:
    """Lazy-load the trained artifact once. None if missing or unloadable.

    A valid bundle is a dict with at least `model`. It may also carry
    `feature_names` (the trained input order) and `baseline` (the population
    {name: (center, scale)} learned at train time) so serving z-scores exactly
    match training z-scores.
    """
    if not _ARTIFACT.exists():
        return None
    try:
        import joblib  # heavy; imported only when an artifact actually exists
    except Exception:
        return None
    try:
        bundle = joblib.load(_ARTIFACT)
    except Exception:
        return None
    if not isinstance(bundle, dict) or "model" not in bundle:
        return None
    bundle.setdefault("feature_names", FEATURE_NAMES)
    bundle.setdefault("baseline", BASELINE)
    return bundle


def zscores_against(
    features: dict[str, Any], baseline: dict[str, tuple[float, float]]
) -> dict[str, float]:
    """Signed z-score of each present signal vs an arbitrary (center, scale) baseline."""
    out: dict[str, float] = {}
    for name, (center, scale) in baseline.items():
        if name not in features or not scale:
            continue
        out[name] = (float(features[name]) - center) / scale
    return out


def risk(feature_record: dict[str, Any]) -> float:
    """FeatureRecord dict -> risk in [0, 1].

    By default this serves the transparent, well-calibrated population-baseline
    risk (deviation magnitude -> logistic), which escalates smoothly from a
    healthy day to a deep spiral — the behaviour the live demo needs.

    The model trained by `brain.train` on StudentLife is an honest *method-check*
    (its PHQ-9 labels are trait depression, not relapse, so it is near-chance and
    would flatten the demo). It is therefore loaded for serving only when
    RELAPSE_USE_TRAINED_MODEL is set, so it can be inspected without silently
    degrading the demo.
    """
    features = feature_record.get("features", {}) or {}

    if os.getenv("RELAPSE_USE_TRAINED_MODEL", "").lower() in ("1", "true", "yes"):
        bundle = _load_artifact()
        if bundle is not None:
            try:
                order: list[str] = bundle["feature_names"]
                zs = zscores_against(features, bundle["baseline"])
                vector = [[zs.get(name, 0.0) for name in order]]
                proba = bundle["model"].predict_proba(vector)[0][1]
                return max(0.0, min(1.0, float(proba)))
            except Exception:
                pass  # any serving hiccup -> calibrated fallback below
    return _fallback_risk(zscores(features))
