# brain/data/loaders.py
"""StudentLife -> tidy per-user-day table -> list[FeatureRecord].

Owns: user discovery, PHQ-9 label join, the single missing-data rule, and conversion
to the frozen FeatureRecord contract.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from brain import config
from brain.contracts import FEATURE_NAMES, FeatureRecord
from brain.data.features import build_user_features

_UID_RE = re.compile(r"_(u\d+)\.csv$")


def discover_users() -> list[str]:
    """User ids that have at least a phonelock log (our densest required source)."""
    lock_dir = config.DATASET_DIR / "sensing" / "phonelock"
    uids = set()
    for p in lock_dir.glob("phonelock_u*.csv"):
        m = _UID_RE.search(p.name)
        if m:
            uids.add(m.group(1))
    return sorted(uids)


# --- Labels (PHQ-9) ----------------------------------------------------------------


def _phq9_score(row: pd.Series, item_cols: list[str]) -> float:
    total, seen = 0.0, 0
    for c in item_cols:
        val = str(row[c]).strip().lower()
        if val in config.PHQ9_RESPONSE_MAP:
            total += config.PHQ9_RESPONSE_MAP[val]
            seen += 1
    if seen == 0:
        return np.nan
    # Scale up if a few items are blank so the cutoff stays comparable.
    return total * (len(item_cols) / seen)


def load_phq9_labels() -> dict[str, int]:
    """uid -> binary label (1 if PHQ-9 >= cutoff). Prefers post survey, falls back to pre."""
    path = config.DATASET_DIR / "survey" / "PHQ-9.csv"
    df = pd.read_csv(path)
    item_cols = [c for c in df.columns if c not in ("uid", "type", "Response")]

    df["_score"] = df.apply(lambda r: _phq9_score(r, item_cols), axis=1)
    labels: dict[str, int] = {}
    for uid, g in df.groupby("uid"):
        by_type = {str(t).lower(): s for t, s in zip(g["type"], g["_score"])}
        score = by_type.get(config.PHQ9_PREFER)
        if score is None or np.isnan(score):
            # fall back to the other timepoint
            other = "pre" if config.PHQ9_PREFER == "post" else "post"
            score = by_type.get(other, np.nan)
        if score is not None and not np.isnan(score):
            labels[str(uid)] = int(score >= config.PHQ9_CUTOFF)
    return labels


# --- Missing-data rule (single source of truth) ------------------------------------


def _apply_missing_rule(df: pd.DataFrame) -> pd.DataFrame:
    """Per config: drop high-missing user-days, then ffill/bfill+median-fill within user."""
    df = df.copy()
    feats = FEATURE_NAMES

    # Count counters that are legitimately 0 (no event that day) as 0, not missing.
    count_like = ["late_night_use_min", "outgoing_comms", "unique_contacts",
                  "screen_unlocks", "near_flagged_min"]
    present = df[feats].notna()

    # Drop user-days with > MAX_MISSING_FRAC of features missing (before any fill).
    miss_frac = 1.0 - present.mean(axis=1)
    df = df[miss_frac <= config.MAX_MISSING_FRAC].copy()
    if df.empty:
        return df

    # Counters -> 0 when missing (absence of events == zero).
    for c in count_like:
        df[c] = df[c].fillna(0.0)

    # Continuous features: ffill/bfill within user (time-ordered), then median fill.
    df = df.sort_values(["user_id", "date"])
    cont = [c for c in feats if c not in count_like]
    df[cont] = (
        df.groupby("user_id")[cont]
        .transform(lambda s: s.ffill().bfill())
    )
    # Per-user median, then global median for any residual.
    for c in cont:
        df[c] = df[c].fillna(df.groupby("user_id")[c].transform("median"))
        df[c] = df[c].fillna(df[c].median())
    return df


# --- Public assembly ---------------------------------------------------------------


def build_feature_table(users: list[str] | None = None) -> pd.DataFrame:
    """Tidy per-user-day feature table after the missing-data rule (NO label attached)."""
    users = users or discover_users()
    frames = []
    for uid in users:
        uf = build_user_features(uid)
        if uf.empty:
            continue
        frames.append(uf)
    if not frames:
        raise RuntimeError("No user features could be built — check dataset path.")

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = _apply_missing_rule(df)

    # Keep only users with enough history.
    counts = df.groupby("user_id")["date"].transform("size")
    df = df[counts >= config.MIN_USER_DAYS]
    return df.sort_values(["user_id", "date"]).reset_index(drop=True)


def load_feature_table(users: list[str] | None = None, verbose: bool = True) -> pd.DataFrame:
    """Full tidy table: one row per user-day with all features + binary PHQ-9 `label`."""
    labels = load_phq9_labels()
    df = build_feature_table(users)

    df["label"] = df["user_id"].map(labels)
    df = df.dropna(subset=["label"]).copy()
    df["label"] = df["label"].astype(int)
    df = df.sort_values(["user_id", "date"]).reset_index(drop=True)

    if verbose:
        _print_summary(df)
    return df


def _print_summary(df: pd.DataFrame) -> None:
    n_users = df["user_id"].nunique()
    pos = df.groupby("user_id")["label"].first()
    print(f"[loaders] {len(df)} user-days across {n_users} users")
    print(f"[loaders] positive users: {int(pos.sum())}/{len(pos)} "
          f"({pos.mean():.1%}) | positive user-days: {df['label'].mean():.1%}")
    rpu = df.groupby("user_id").size()
    print(f"[loaders] rows/user: min={rpu.min()} median={int(rpu.median())} max={rpu.max()}")
    miss = df[FEATURE_NAMES].isna().mean()
    if miss.any():
        print(f"[loaders] residual missingness:\n{miss[miss > 0].to_string()}")
    else:
        print("[loaders] residual missingness: none")


def to_feature_records(df: pd.DataFrame) -> list[FeatureRecord]:
    """Tidy table -> list[FeatureRecord] (the frozen contract type)."""
    records = []
    for _, r in df.iterrows():
        records.append(FeatureRecord(
            user_id=str(r["user_id"]),
            date=r["date"],
            sleep_hours=float(r["sleep_hours"]),
            late_night_use_min=float(r["late_night_use_min"]),
            outgoing_comms=int(r["outgoing_comms"]),
            unique_contacts=int(r["unique_contacts"]),
            location_entropy=float(r["location_entropy"]),
            time_at_home_frac=float(r["time_at_home_frac"]),
            screen_unlocks=int(r["screen_unlocks"]),
            near_flagged_min=float(r["near_flagged_min"]),
            label=int(r["label"]) if "label" in r and not pd.isna(r["label"]) else None,
        ))
    return records
