# brain/models/baseline.py
"""Personal baseline: per-user rolling normal (median + IQR) -> robust z-scores.

This is the N-of-1 core. Each feature is compared to that user's OWN normal,
split weekday vs weekend, so "high for them" matters more than "high in general".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from brain.contracts import FEATURE_NAMES

# Features where we model a personal baseline (near_flagged_min is constant 0 here).
BASELINE_FEATURES = [f for f in FEATURE_NAMES if f != "near_flagged_min"]
ZSCORE_COLS = [f"{f}_z" for f in BASELINE_FEATURES]

# Canonical rolling-baseline hyper-params. ONE definition shared by every caller
# (model training, SHAP drivers, ablation) so explanations can never disagree with
# predictions.
BASELINE_WINDOW = 21        # trailing days of personal history to summarize
BASELINE_MIN_PERIODS = 3    # need this many prior days before we trust the personal stat

_EPS = 1e-6


def _robust_stats(s: pd.Series) -> tuple[float, float]:
    """Median and IQR (75th-25th pct) of a series, IQR floored away from 0."""
    median = float(s.median())
    iqr = float(s.quantile(0.75) - s.quantile(0.25))
    if not np.isfinite(iqr) or iqr < _EPS:
        # fall back to scaled MAD, then std, then 1.0
        mad = float((s - median).abs().median())
        iqr = 1.4826 * mad if mad > _EPS else float(s.std(ddof=0) or 1.0)
        iqr = max(iqr, _EPS)
    return median, iqr


class PersonalBaseline:
    """Learns per-(user, is_weekend) median+IQR, then z-scores each feature."""

    def __init__(self, features: list[str] | None = None):
        self.features = features or BASELINE_FEATURES
        self.stats_: dict[tuple[str, bool, str], tuple[float, float]] = {}
        self.global_stats_: dict[str, tuple[float, float]] = {}

    @staticmethod
    def _is_weekend(dates: pd.Series) -> pd.Series:
        return pd.to_datetime(dates).dt.dayofweek >= 5

    def fit(self, df: pd.DataFrame) -> "PersonalBaseline":
        wk = self._is_weekend(df["date"])
        for feat in self.features:
            self.global_stats_[feat] = _robust_stats(df[feat])
        for (uid, is_wend), g in df.assign(_wend=wk).groupby(["user_id", "_wend"]):
            for feat in self.features:
                self.stats_[(uid, bool(is_wend), feat)] = _robust_stats(g[feat])
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Append `<feat>_z` columns. Unseen user/feature falls back to global stats."""
        out = df.copy()
        wk = self._is_weekend(out["date"]).to_numpy()
        uids = out["user_id"].to_numpy()
        for feat in self.features:
            vals = out[feat].to_numpy(dtype="float64")
            z = np.empty(len(out), dtype="float64")
            for i in range(len(out)):
                med, iqr = self.stats_.get(
                    (uids[i], bool(wk[i]), feat), self.global_stats_[feat]
                )
                z[i] = (vals[i] - med) / iqr
            out[f"{feat}_z"] = np.clip(z, -8.0, 8.0)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)


def _scalar_is_weekend(date) -> bool:
    return pd.Timestamp(date).dayofweek >= 5


def population_stats(
    df: pd.DataFrame, features: list[str] | None = None
) -> dict[str, tuple[float, float]]:
    """Per-feature robust (median, IQR) over the whole population.

    Used as the cold-start fallback for users with too little personal history.
    Persist this alongside the model so serving uses the same fallback as training.
    """
    features = features or BASELINE_FEATURES
    return {feat: _robust_stats(df[feat]) for feat in features}


def to_zscores(
    record,
    history: pd.DataFrame,
    features: list[str] | None = None,
    *,
    window: int = BASELINE_WINDOW,
    min_periods: int = BASELINE_MIN_PERIODS,
    split_weekend: bool = True,
    pop_stats: dict[str, tuple[float, float]] | None = None,
) -> dict[str, float]:
    """Z-score ONE day's `record` against that user's OWN prior `history`.

    This is THE canonical personal-baseline transform — the on-device N-of-1 view:
    "how abnormal is today *for this person*". Model training, SHAP drivers, and the
    ablation all route through this exact function, so explanations can never disagree
    with predictions.

    Parameters
    ----------
    record   : Mapping/Series of feature -> value for today (must include `date`).
    history  : that user's STRICTLY EARLIER day rows (feature cols + `date`); order-agnostic.
    pop_stats: optional population (median, IQR) fallback for cold-start days
               (see `population_stats`). If absent, falls back to (0, 1).

    Returns `{f"{feat}_z": value}` for each feature, clipped to +/-8.
    """
    features = features or BASELINE_FEATURES
    rec = record if isinstance(record, pd.Series) else pd.Series(record)

    hist = history
    if split_weekend and len(hist):
        same = PersonalBaseline._is_weekend(hist["date"]).to_numpy() == _scalar_is_weekend(rec["date"])
        hist = hist.loc[same]
    if len(hist):
        hist = hist.sort_values("date").tail(window)

    out: dict[str, float] = {}
    for feat in features:
        vals = hist[feat].dropna() if feat in hist.columns else pd.Series(dtype="float64")
        if len(vals) >= min_periods:
            med, iqr = _robust_stats(vals)
        elif pop_stats is not None and feat in pop_stats:
            med, iqr = pop_stats[feat]
        else:
            med, iqr = 0.0, 1.0
        z = (float(rec[feat]) - med) / max(iqr, _EPS)
        out[f"{feat}_z"] = float(np.clip(z, -8.0, 8.0))
    return out


def add_rolling_zscores(
    df: pd.DataFrame,
    features: list[str] | None = None,
    window: int = BASELINE_WINDOW,
    min_periods: int = BASELINE_MIN_PERIODS,
    split_weekend: bool = True,
    pop_stats: dict[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Vectorized table version of `to_zscores`: append causal `<feat>_z` columns.

    For every (user, day) it scores the day against that user's STRICTLY EARLIER days
    by calling `to_zscores`, so the table-level output is identical, row for row, to
    the single-record API used at serve time. No future leakage; labels unused.

    `pop_stats` defaults to population stats computed from `df` (pass an explicit dict
    — e.g. the model's stored stats — to keep train/serve cold-start identical).
    """
    features = features or BASELINE_FEATURES
    if pop_stats is None:
        pop_stats = population_stats(df, features)

    out = df.sort_values(["user_id", "date"]).reset_index(drop=True).copy()
    z_rows: list[dict[str, float]] = [None] * len(out)  # type: ignore[list-item]

    pos = 0
    for _, g in out.groupby("user_id", sort=False):
        hist_cols = g[["date", *features]]
        for k in range(len(g)):
            record = g.iloc[k]
            history = hist_cols.iloc[:k]  # strictly earlier days for this user
            z_rows[pos] = to_zscores(
                record, history, features,
                window=window, min_periods=min_periods,
                split_weekend=split_weekend, pop_stats=pop_stats,
            )
            pos += 1

    z_df = pd.DataFrame(z_rows, index=out.index)
    return pd.concat([out, z_df], axis=1)
