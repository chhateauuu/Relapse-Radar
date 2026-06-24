# brain/data/features.py
"""Raw StudentLife logs -> per-user-day feature fields (the FeatureRecord columns).

All features are phone-passive, metadata only. One function per raw source, plus
`build_user_features(uid)` that joins them into a tidy per-day table for one user.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from brain import config
from brain.contracts import FEATURE_NAMES

# Local-time component series helpers ------------------------------------------------


def _to_local(epoch: pd.Series) -> pd.Series:
    """Unix seconds -> tz-aware local datetime."""
    dt = pd.to_datetime(epoch, unit="s", utc=True, errors="coerce")
    return dt.dt.tz_convert(config.LOCAL_TZ)


def _read_csv(path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        # index_col=False: StudentLife CSVs have trailing commas; without this pandas
        # silently shifts columns by consuming the first field as the index.
        return pd.read_csv(path, skip_blank_lines=True, index_col=False)
    except Exception:
        return pd.DataFrame()


def _empty_series(name: str) -> pd.Series:
    s = pd.Series(dtype="float64", name=name)
    s.index.name = "date"
    return s


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """Return a column as a Series, or an all-NaN Series if the column is absent."""
    if name in df.columns:
        return df[name]
    return pd.Series(index=df.index, dtype="object")


# Interval sources: phonelock (start,end) ------------------------------------------


def _phonelock_features(uid: str) -> pd.DataFrame:
    """sleep_hours, late_night_use_min, screen_unlocks from lock intervals."""
    df = _read_csv(config.DATASET_DIR / "sensing" / "phonelock" / f"phonelock_{uid}.csv")
    cols = ["sleep_hours", "late_night_use_min", "screen_unlocks"]
    if df.empty or not {"start", "end"}.issubset(df.columns):
        out = pd.DataFrame(columns=cols)
        out.index.name = "date"
        return out

    start = _to_local(df["start"])
    end = _to_local(df["end"])
    dur_min = (df["end"] - df["start"]).clip(lower=0) / 60.0

    work = pd.DataFrame({
        "start": start,
        "end": end,
        "dur_min": dur_min,
        "start_date": start.dt.normalize().dt.tz_localize(None),
        "start_hour": start.dt.hour,
    }).dropna(subset=["start", "end"])

    # screen_unlocks: each lock interval ~ one unlock event, by start date.
    unlocks = work.groupby("start_date").size().rename("screen_unlocks")

    # sleep_hours: longest night-time lock interval per day (proxy for main sleep gap).
    lo, hi = config.NIGHT_SLEEP_WINDOW  # (21, 11)
    is_night = (work["start_hour"] >= lo) | (work["start_hour"] < hi)
    night = work[is_night & (work["dur_min"] >= 120)]
    sleep = (night.groupby("start_date")["dur_min"].max() / 60.0).clip(upper=14.0)
    sleep = sleep.rename("sleep_hours")

    # late_night_use_min: minutes in [1,5) local NOT covered by a lock interval.
    ln_lo, ln_hi = config.LATE_NIGHT_WINDOW
    locked_min = _locked_minutes_in_window(work, ln_lo, ln_hi)
    window_min = (ln_hi - ln_lo) * 60.0
    late = (window_min - locked_min).clip(lower=0.0).rename("late_night_use_min")

    out = pd.concat([sleep, late, unlocks], axis=1)
    out.index.name = "date"
    return out


def _locked_minutes_in_window(work: pd.DataFrame, hour_lo: int, hour_hi: int) -> pd.Series:
    """Per date, minutes of lock-interval overlap with [hour_lo, hour_hi) local."""
    rows = []
    for _, r in work.iterrows():
        s, e = r["start"], r["end"]
        # iterate the (at most 2) dates this interval can touch in the window
        for day in pd.date_range(s.normalize(), e.normalize(), freq="D"):
            w_start = day + pd.Timedelta(hours=hour_lo)
            w_end = day + pd.Timedelta(hours=hour_hi)
            ov = (min(e, w_end) - max(s, w_start)).total_seconds() / 60.0
            if ov > 0:
                rows.append((day.tz_localize(None), ov))
    if not rows:
        return _empty_series("locked_min")
    g = pd.DataFrame(rows, columns=["date", "locked_min"]).groupby("date")["locked_min"].sum()
    g.index.name = "date"
    return g


# Comms sources: sms + call_log -----------------------------------------------------


def _comms_features(uid: str) -> pd.DataFrame:
    """outgoing_comms (sent texts + outgoing calls) and unique_contacts per day."""
    sms = _read_csv(config.DATASET_DIR / "sms" / f"sms_{uid}.csv")
    calls = _read_csv(config.DATASET_DIR / "call_log" / f"call_log_{uid}.csv")

    frames = []
    if not sms.empty and "timestamp" in sms.columns:
        ts = _to_local(sms["timestamp"])
        contact = _col(sms, "MESSAGES_address").astype(str)
        mtype = pd.to_numeric(_col(sms, "MESSAGES_type"), errors="coerce")
        frames.append(pd.DataFrame({
            "date": ts.dt.normalize().dt.tz_localize(None),
            "contact": contact,
            "outgoing": (mtype == 2).fillna(False),
        }))
    if not calls.empty and "timestamp" in calls.columns:
        ts = _to_local(calls["timestamp"])
        contact = _col(calls, "CALLS_number").astype(str)
        ctype = pd.to_numeric(_col(calls, "CALLS_type"), errors="coerce")
        frames.append(pd.DataFrame({
            "date": ts.dt.normalize().dt.tz_localize(None),
            "contact": contact,
            "outgoing": (ctype == 2).fillna(False),
        }))

    if not frames:
        out = pd.DataFrame(columns=["outgoing_comms", "unique_contacts"])
        out.index.name = "date"
        return out

    ev = pd.concat(frames, ignore_index=True).dropna(subset=["date"])
    ev["contact"] = ev["contact"].replace({"nan": np.nan, "": np.nan})

    outgoing = ev[ev["outgoing"]].groupby("date").size().rename("outgoing_comms")
    contacts = (
        ev.dropna(subset=["contact"]).groupby("date")["contact"].nunique().rename("unique_contacts")
    )
    out = pd.concat([outgoing, contacts], axis=1)
    out.index.name = "date"
    return out


# GPS source ------------------------------------------------------------------------


def _gps_features(uid: str) -> pd.DataFrame:
    """location_entropy and time_at_home_frac per day from GPS fixes."""
    df = _read_csv(config.DATASET_DIR / "sensing" / "gps" / f"gps_{uid}.csv")
    cols = ["location_entropy", "time_at_home_frac"]
    if df.empty or not {"time", "latitude", "longitude"}.issubset(df.columns):
        out = pd.DataFrame(columns=cols)
        out.index.name = "date"
        return out

    ts = _to_local(df["time"])
    lat = pd.to_numeric(df["latitude"], errors="coerce").round(config.GPS_GRID_DECIMALS)
    lon = pd.to_numeric(df["longitude"], errors="coerce").round(config.GPS_GRID_DECIMALS)
    g = pd.DataFrame({
        "date": ts.dt.normalize().dt.tz_localize(None),
        "hour": ts.dt.hour,
        "cell": lat.astype("string") + "," + lon.astype("string"),
    }).dropna(subset=["date", "cell"])
    g = g[g["cell"].str.contains("<NA>") == False]  # noqa: E712
    if g.empty:
        out = pd.DataFrame(columns=cols)
        out.index.name = "date"
        return out

    # Home cell = most frequent cell during night hours across the whole study.
    h_lo, h_hi = config.HOME_NIGHT_WINDOW
    night = g[(g["hour"] >= h_lo) & (g["hour"] < h_hi)]
    home_cell = (night["cell"].mode().iloc[0] if not night.empty else g["cell"].mode().iloc[0])

    entropy = g.groupby("date")["cell"].apply(_shannon_entropy).rename("location_entropy")
    home_frac = (
        g.assign(at_home=(g["cell"] == home_cell))
        .groupby("date")["at_home"].mean()
        .rename("time_at_home_frac")
    )
    out = pd.concat([entropy, home_frac], axis=1)
    out.index.name = "date"
    return out


def _shannon_entropy(cells: pd.Series) -> float:
    counts = cells.value_counts().to_numpy(dtype="float64")
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


# Public API ------------------------------------------------------------------------


def build_user_features(uid: str) -> pd.DataFrame:
    """All FeatureRecord feature columns for one user, indexed by date (one row/day)."""
    parts = [
        _phonelock_features(uid),
        _comms_features(uid),
        _gps_features(uid),
    ]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=["user_id", "date", *FEATURE_NAMES])

    df = pd.concat(parts, axis=1)
    df = df[~df.index.isna()]
    df["near_flagged_min"] = 0.0  # not in datasets; injected by the demo simulator

    # Ensure every contract feature column exists, in canonical order.
    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = np.nan
    df = df.sort_index()
    df = df.reset_index().rename(columns={"index": "date"})
    df["user_id"] = uid
    return df[["user_id", "date", *FEATURE_NAMES]]
