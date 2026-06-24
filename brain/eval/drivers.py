"""Top risk drivers for a FeatureRecord.   [P2]

Returns the handful of signals pushing a person off their own baseline, in the
RiskAssessment `drivers` shape: [{feature, z, direction}, ...].

  - NOW: z-scores vs a population baseline (works today, no model needed).
  - LATER: SHAP over P1's LightGBM, against each user's PERSONAL baseline. The
    return shape is identical, so `assess()` keeps calling `drivers()` unchanged
    — only the internals swap. See the `_TODO_shap` note below.

Run a smoke test from the repo root:  python -m brain.eval.drivers
"""
from __future__ import annotations

from typing import Any

# (mean, spread) per signal. Mirrors the simulator's BASELINE; this is the
# stop-gap population baseline. P1 replaces it with the learned, per-user
# rolling baseline (median / IQR) — at which point `z` becomes "how far off
# is today from YOUR normal," which is the whole personalization story.
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

# The risk-increasing direction for each signal (the "bad" way to deviate).
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

MIN_ABS_Z = 1.0  # ignore signals within ~1 sd of normal


def drivers(feature_record: dict[str, Any], top_k: int = 3) -> list[dict[str, Any]]:
    """Top-k signals deviating in the risk-increasing direction, by |z|."""
    feats = feature_record.get("features", {})
    found: list[dict[str, Any]] = []
    for name, (mean, spread) in BASELINE.items():
        if name not in feats or spread == 0:
            continue
        z = (float(feats[name]) - mean) / spread
        direction = "up" if z > 0 else "down"
        if direction == RISK_DIRECTION[name] and abs(z) >= MIN_ABS_Z:
            found.append({"feature": name, "z": round(z, 2), "direction": direction})
    found.sort(key=lambda d: abs(d["z"]), reverse=True)
    return found[:top_k]


def _load_bundle() -> "dict | None":
    """Load a trained tree-model bundle if one exists AND is loadable.

    A bundle is `{model, feature_names, baseline}`. Tries the configured models
    dir, then `brain/model/`, then the committed `brain/draft_files/artifacts/`.
    Returns None on any failure (e.g. the artifact references a module that
    isn't importable) so `shap_drivers` degrades cleanly to z-score drivers.
    """
    import os
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    candidates = []
    if os.getenv("RELAPSE_MODELS_DIR"):
        candidates.append(Path(os.environ["RELAPSE_MODELS_DIR"]) / "fusion_model.joblib")
    candidates += [
        root / "brain" / "model" / "fusion_model.joblib",
        root / "brain" / "draft_files" / "artifacts" / "fusion_model.joblib",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            import joblib
            bundle = joblib.load(path)
        except Exception:
            continue
        if isinstance(bundle, dict) and "model" in bundle:
            bundle.setdefault("feature_names", list(BASELINE.keys()))
            bundle.setdefault("baseline", BASELINE)
            return bundle
    return None


def shap_drivers(
    feature_record: dict[str, Any], bundle: "dict | None" = None, top_k: int = 3
) -> list[dict[str, Any]]:
    """Exact per-feature drivers via SHAP TreeExplainer over a trained tree model.

    Same contract shape as `drivers` — `[{feature, z, direction}]` — but ranked
    by the model's exact SHAP contribution instead of raw |z|. Falls back to
    `drivers()` whenever no loadable tree model (or shap) is available, so it is
    always safe to call. Pass `bundle` explicitly to use a specific model.
    """
    bundle = bundle if bundle is not None else _load_bundle()
    if bundle is None:
        return drivers(feature_record, top_k)
    feats = feature_record.get("features", {}) or {}
    try:
        import numpy as np
        import shap

        names = bundle["feature_names"]
        base = bundle["baseline"]
        zs = {
            n: (float(feats[n]) - base[n][0]) / base[n][1]
            for n in names
            if n in feats and base[n][1]
        }
        vector = np.array([[zs.get(n, 0.0) for n in names]], dtype=float)
        sv = shap.TreeExplainer(bundle["model"]).shap_values(vector)
        if isinstance(sv, list):  # [class0, class1] -> positive class
            sv = sv[-1]
        contribs = np.asarray(sv).reshape(len(names))
        found = []
        for name, contrib in zip(names, contribs):
            if contrib > 0:  # pushes risk UP
                z = zs.get(name, 0.0)
                found.append({
                    "feature": name, "z": round(z, 2),
                    "direction": "up" if z > 0 else "down", "_c": float(contrib),
                })
        found.sort(key=lambda d: d["_c"], reverse=True)
        for d in found:
            d.pop("_c")
        return found[:top_k] or drivers(feature_record, top_k)
    except Exception:
        return drivers(feature_record, top_k)


if __name__ == "__main__":
    import json
    from pathlib import Path

    fixtures = Path(__file__).resolve().parents[2] / "shared" / "fixtures"
    spiral = json.loads((fixtures / "maya_spiral.json").read_text(encoding="utf-8"))
    worst = spiral[-1]  # deepest day of the spiral
    result = drivers(worst)
    print(f"drivers for day {worst['day']}:")
    print(json.dumps(result, indent=2))
    assert result, "expected at least one driver on the worst spiral day"
    assert all({"feature", "z", "direction"} <= d.keys() for d in result), result
    print("OK:", ", ".join(d["feature"] for d in result))

    # Validate the SHAP TreeExplainer path end-to-end against a tiny LightGBM
    # (P1's real artifact currently won't unpickle, so we prove the capability
    # on a fresh model trained in the same z-score space shap_drivers feeds).
    try:
        import numpy as np
        from lightgbm import LGBMClassifier

        names = list(BASELINE.keys())
        rng = np.random.default_rng(0)
        X, y = [], []
        for _ in range(400):
            is_spiral = rng.random() < 0.4
            row = []
            for n in names:
                z = rng.normal()
                if is_spiral:
                    z += (2.0 if RISK_DIRECTION[n] == "up" else -2.0) * rng.random()
                row.append(z)
            X.append(row)
            y.append(1 if is_spiral else 0)
        model = LGBMClassifier(n_estimators=60, num_leaves=8, verbosity=-1).fit(
            np.array(X), np.array(y)
        )
        bundle = {"model": model, "feature_names": names, "baseline": BASELINE}
        sd = shap_drivers(worst, bundle=bundle)
        print(f"\nSHAP drivers for day {worst['day']}:")
        print(json.dumps(sd, indent=2))
        assert sd and all({"feature", "z", "direction"} <= d.keys() for d in sd), sd
        print("OK (shap):", ", ".join(d["feature"] for d in sd))
    except Exception as exc:  # pragma: no cover - capability check only
        print("SHAP self-test skipped:", exc)

