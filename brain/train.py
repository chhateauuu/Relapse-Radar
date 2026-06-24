# brain/train.py
"""Train the fusion risk model on StudentLife + emit the ROC/AUC chart.   [P1]

Pipeline:
  1. Load StudentLife into a tidy per-user-day table with a binary PHQ-9 label
     (brain.data.loaders).
  2. z-score every feature against the shared team baseline (brain.scorer.BASELINE)
     — the SAME normalizer assess() serves with, so train and serve match and the
     maya demo stays on-scale.
  3. Train a gradient-boosting classifier on the z-score vector -> risk.
     Prefers LightGBM; falls back to sklearn GradientBoosting, then LogisticRegression
     (so it runs anywhere, incl. ARM64 where LightGBM has no wheel).
  4. Honest AUC via GroupKFold (group = user_id; no user in both train and test).
  5. Save {model, feature_names, baseline} to brain/models/fusion_model.joblib and
     the ROC chart to brain/notebooks/roc_auc.png.

Run from the repo root:  python -m brain.train
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from brain import config, scorer
from brain.data.loaders import load_feature_table

FEATURE_NAMES = scorer.FEATURE_NAMES


def _to_zscore_matrix(df: pd.DataFrame) -> np.ndarray:
    """Each feature -> z vs the shared team baseline; rows aligned to FEATURE_NAMES."""
    cols = []
    for name in FEATURE_NAMES:
        center, scale = scorer.BASELINE[name]
        scale = scale or 1.0
        cols.append((df[name].astype("float64") - center) / scale)
    return np.column_stack(cols)


def _build_classifier():
    """Best available gradient-boosting classifier, with graceful fallbacks."""
    try:
        import lightgbm as lgb  # noqa: F401

        return ("lightgbm", lgb.LGBMClassifier(
            objective="binary", n_estimators=300, learning_rate=0.03,
            num_leaves=15, max_depth=4, min_child_samples=20,
            subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
            reg_lambda=1.0, random_state=config.RANDOM_SEED, n_jobs=-1, verbose=-1,
        ))
    except Exception:
        pass
    try:
        from sklearn.ensemble import GradientBoostingClassifier

        return ("sklearn-gboost", GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=3,
            subsample=0.85, random_state=config.RANDOM_SEED,
        ))
    except Exception:
        pass
    from sklearn.linear_model import LogisticRegression

    return ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced"))


def _fit(estimator, name: str, X: np.ndarray, y: np.ndarray):
    """Fit, passing class weighting where the estimator supports it."""
    if name == "lightgbm":
        pos = max(int(y.sum()), 1)
        neg = max(int((1 - y).sum()), 1)
        estimator.set_params(scale_pos_weight=neg / pos)
    estimator.fit(X, y)
    return estimator


def _cv_auc(name: str, X: np.ndarray, y: np.ndarray, groups: np.ndarray):
    """Honest out-of-fold AUC with GroupKFold by user. Returns (auc, y_true, y_score)."""
    from sklearn.base import clone
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold

    n_groups = len(np.unique(groups))
    n_splits = min(config.N_SPLITS, n_groups)
    if n_splits < 2:
        return float("nan"), y, np.full_like(y, fill_value=y.mean(), dtype="float64")

    oof = np.zeros(len(y), dtype="float64")
    gkf = GroupKFold(n_splits=n_splits)
    for tr, te in gkf.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            oof[te] = y[tr].mean()
            continue
        _, fresh = _build_classifier()
        fresh = clone(fresh)
        _fit(fresh, name, X[tr], y[tr])
        oof[te] = fresh.predict_proba(X[te])[:, 1]
    try:
        auc = roc_auc_score(y, oof)
    except ValueError:
        auc = float("nan")
    return auc, y, oof


def _save_roc(y_true: np.ndarray, y_score: np.ndarray, auc: float, backend: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.metrics import roc_curve
    except Exception as exc:  # pragma: no cover
        print(f"[train] skipped ROC chart ({exc})")
        return

    config.NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.NOTEBOOKS_DIR / "roc_auc.png"
    fpr, tpr, _ = roc_curve(y_true, y_score)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, lw=2, label=f"{backend} (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="chance")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("Relapse Radar — risk model ROC (StudentLife, GroupKFold)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out, dpi=130)
    plt.close()
    print(f"[train] ROC chart -> {out}")


def _save_artifact(model, backend: str) -> None:
    import joblib

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.MODELS_DIR / "fusion_model.joblib"
    joblib.dump(
        {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "baseline": scorer.BASELINE,
            "backend": backend,
        },
        out,
    )
    print(f"[train] model artifact -> {out}  (backend: {backend})")


def main() -> None:
    print(f"[train] dataset: {config.DATASET_DIR}")
    df = load_feature_table()
    if df["label"].nunique() < 2:
        raise RuntimeError("Need both labels present to train; got a single class.")

    X = _to_zscore_matrix(df)
    y = df["label"].to_numpy(dtype="int64")
    groups = df["user_id"].to_numpy()

    backend, _ = _build_classifier()
    print(f"[train] classifier backend: {backend}")

    auc, y_true, y_score = _cv_auc(backend, X, y, groups)
    print(f"[train] GroupKFold AUC: {auc:.3f}  (target literature 0.70-0.88; "
          f"StudentLife is daily-affect, so chance-ish is expected and honest)")

    # Final model on all data for serving.
    _, model = _build_classifier()
    _fit(model, backend, X, y)

    _save_artifact(model, backend)
    _save_roc(y_true, y_score, auc, backend)
    print("[train] done.")


if __name__ == "__main__":
    main()
