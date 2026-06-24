"""brain.eval — P2's detection + proof layer.

Exposes the two functions P1's `assess()` calls to fill the parts of a
RiskAssessment that P2 owns:

  - `detect(risk_series, days)` -> {state, changepoint}   (change-point + state)
  - `drivers(feature_record)`   -> [{feature, z, direction}, ...]  (top signals)

See ../../shared/contracts.md for the exact RiskAssessment shape.
"""
from __future__ import annotations

from .detect import detect, state_for
from .drivers import drivers, shap_drivers

__all__ = ["detect", "state_for", "drivers", "shap_drivers"]
