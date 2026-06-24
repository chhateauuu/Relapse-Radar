# brain/models/fusion.py
"""LightGBM risk model on personal z-scores, with SHAP-based drivers.

Bundles the PersonalBaseline + LightGBM classifier so train/serve use identical
feature construction. Produces `risk` (0-1) and human-readable `drivers`.
"""
from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from brain import config
from brain.models.baseline import (
    BASELINE_FEATURES,
    ZSCORE_COLS,
    add_rolling_zscores,
    population_stats,
)

# Friendly phrases per signal, as (text_when_above_typical, text_when_below_typical).
_DRIVER_TEXT = {
    "sleep_hours_z": ("more sleep than usual", "less sleep than usual"),
    "late_night_use_min_z": ("more late-night phone use", "less late-night phone use"),
    "outgoing_comms_z": ("more messages/calls than usual", "fewer messages/calls than usual"),
    "unique_contacts_z": ("talking to more people", "talking to fewer people (social withdrawal)"),
    "location_entropy_z": ("going more places than usual", "going fewer places (routine collapse)"),
    "time_at_home_frac_z": ("more time at home than usual", "less time at home than usual"),
    "screen_unlocks_z": ("more phone checking (agitation)", "less phone checking than usual"),
}

_DEFAULT_PARAMS = dict(
    objective="binary",
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=15,
    max_depth=4,
    min_child_samples=20,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=config.RANDOM_SEED,
    n_jobs=-1,
    verbose=-1,
)


@dataclass
class TrainResult:
    auc: float
    n_train: int
    n_test: int


class FusionModel:
    """PersonalBaseline (z-scores) + LightGBM. `personal=False` -> raw-feature population model."""

    def __init__(self, personal: bool = True, params: dict | None = None):
        self.personal = personal
        self.params = {**_DEFAULT_PARAMS, **(params or {})}
        self.pop_stats_: dict | None = None
        self.model_: lgb.LGBMClassifier | None = None
        self.feature_cols_: list[str] = ZSCORE_COLS if personal else BASELINE_FEATURES
        self.train_median_: pd.Series | None = None
        self._explainer = None

    # --- feature construction -------------------------------------------------------
    def _design(self, df: pd.DataFrame, fit: bool) -> pd.DataFrame:
        if not self.personal:
            return df[self.feature_cols_].astype("float64")
        # Personal path: canonical causal per-user rolling z-scores (same function the
        # SHAP drivers and the ablation use -> explanations match predictions exactly).
        if fit:
            self.pop_stats_ = population_stats(df)
        assert self.pop_stats_ is not None, "baseline stats not fitted"
        z = add_rolling_zscores(df, pop_stats=self.pop_stats_)
        return z[self.feature_cols_].astype("float64")

    # --- train / predict ------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "FusionModel":
        X = self._design(df, fit=True)
        self.train_median_ = X.median()
        y = df["label"].astype(int).to_numpy()
        pos = max(int(y.sum()), 1)
        neg = max(int((1 - y).sum()), 1)
        self.model_ = lgb.LGBMClassifier(
            scale_pos_weight=neg / pos, **self.params
        )
        self.model_.fit(X, y)
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        assert self.model_ is not None, "model not fitted"
        X = self._design(df, fit=False)
        return self.model_.predict_proba(X)[:, 1]

    # --- explanations ---------------------------------------------------------------
    def drivers(self, df: pd.DataFrame, top_k: int = 3) -> list[list[str]]:
        """Top-k SHAP drivers per row as human-readable phrases."""
        import shap  # local import keeps module import cheap

        assert self.model_ is not None, "model not fitted"
        X = self._design(df, fit=False)
        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model_)
        sv = self._explainer.shap_values(X)
        if isinstance(sv, list):  # older shap returns [neg, pos]
            sv = sv[1]
        sv = np.asarray(sv)

        out: list[list[str]] = []
        for i in range(X.shape[0]):
            order = np.argsort(-np.abs(sv[i]))
            phrases: list[str] = []
            for j in order[:top_k]:
                if sv[i, j] <= 0:
                    continue  # only signals that PUSH risk up
                col = self.feature_cols_[j]
                med = float(self.train_median_[col]) if self.train_median_ is not None else 0.0
                phrases.append(self._phrase(col, X.iloc[i, j] - med))
            out.append(phrases or ["no single dominant signal"])
        return out

    @staticmethod
    def _phrase(col: str, value: float) -> str:
        key = col if col.endswith("_z") else f"{col}_z"
        if key in _DRIVER_TEXT:
            high, low = _DRIVER_TEXT[key]
            return high if value >= 0 else low
        return col.replace("_z", "").replace("_", " ")
