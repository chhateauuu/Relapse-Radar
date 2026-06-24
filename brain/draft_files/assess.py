# assess.py
"""The function everyone imports. Loads the trained model and scores one FeatureRecord.

If no trained artifact exists yet, falls back to the deterministic stub so teammates
are never blocked. Same signature as the Phase-0 stub.
"""
from __future__ import annotations

import functools

import pandas as pd

from brain import config
from brain.contracts import FEATURE_NAMES, FeatureRecord, RiskAssessment
from brain.data.fixtures import stub_assess

_ARTIFACT = config.ARTIFACTS_DIR / "fusion_model.joblib"


@functools.lru_cache(maxsize=1)
def _load_model():
    """Load the trained FusionModel artifact once, or None if it doesn't exist."""
    if not _ARTIFACT.exists():
        return None
    import joblib
    return joblib.load(_ARTIFACT)["model"]


def _record_to_frame(record: FeatureRecord) -> pd.DataFrame:
    row = {"user_id": record.user_id, "date": pd.to_datetime(record.date).date()}
    for f in FEATURE_NAMES:
        row[f] = getattr(record, f)
    return pd.DataFrame([row])


def assess(record: FeatureRecord) -> RiskAssessment:
    """FeatureRecord -> RiskAssessment. Fills `risk` + `drivers` (P2 fills state later)."""
    model = _load_model()
    if model is None:
        return stub_assess(record)

    df = _record_to_frame(record)
    risk = float(model.predict_proba(df)[0])
    drivers = model.drivers(df, top_k=3)[0]
    return RiskAssessment(
        user_id=record.user_id,
        date=record.date,
        risk=risk,
        drivers=drivers,
    )


if __name__ == "__main__":
    from brain.data.fixtures import sample_records

    for rec in sample_records():
        ra = assess(rec)
        print(f"{ra.user_id}: risk={ra.risk:.3f} drivers={ra.drivers}")
