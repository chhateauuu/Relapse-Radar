# brain/data/features.py
"""Raw StudentLife logs -> per-user-day feature rows (the FROZEN FeatureRecord fields).

All features are phone-passive metadata. One function per raw source, plus
`build_user_features(uid)` that joins them into a tidy per-day table for one user.

Feature names are the canonical contract names from shared/contracts.md:
  sleep_hours, late_night_min, screen_time_min, unlocks, outgoing_msgs,
  unique_contacts, location_entropy, time_at_home_pct, dwell_flagged_min, steps
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from brain import config
from brain.scorer import FEATURE_NAMES


# --- helpers -----------------------------------------------------------------------


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
        df = pd.read_csv(path, skip_blank_lines=True, index_col=False)
    except Exception:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]  # headers have stray spaces
    return df


def _empty(cols: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(columns=cols)
    out.index.name = "date"
    return out


# --- phonelock (start,end intervals): sleep, late-night, unlocks, screen_time ------


def _phonelock_features(uid: str) -> pd.DataFrame:
    """sleep_hours, late_night_min, unlocks, screen_time_min from lock intervals.

    A lock interval is screen-OFF time. So: unlocks = number of intervals; sleep =
    longest overnight OFF gap; screen_time = minutes of the day NOT locked; late-night
    = minutes between 1-5am NOT locked (i.e. awake/using).
    """
    cols = ["sleep_hours", "late_night_min", "unlocks", "screen_time_min"]
    df = _read_csv(config.DATASET_DIR / "sensing" / "phonelock" / f"phonelock_{uid}.csv")
    if df.empty or not {"start", "end"}.issubset(df.columns):
        return _empty(cols)

    start = _to_local(df["start"])
    end = _to_local(df["end"])
    dur_min = (pd.to_numeric(df["end"], errors="coerce")
               - pd.to_numeric(df["start"], errors="coerce")).clip(lower=0) / 60.0

    work = pd.DataFrame({
        "start": start,
        "end": end,
        "dur_min": dur_min,
        "date": start.dt.normalize().dt.tz_localize(None),
        "hour": start.dt.hour,
    }).dropna(subset=["start", "end", "date"])
    if work.empty:
        return _empty(cols)

    # unlocks: each lock interval == one screen-off, ~one unlock when it ends.
    unlocks = work.groupby("date").size().rename("unlocks")

    # sleep_hours: longest night-time OFF interval per day (main sleep gap proxy).
    lo, hi = config.NIGHT_SLEEP_WINDOW  # (21, 11)
    is_night = (work["hour"] >= lo) | (work["hour"] < hi)
    night = work[is_night & (work["dur_min"] >= 120)]
    sleep = (night.groupby("date")["dur_min"].max() / 60.0).clip(upper=14.0).rename("sleep_hours")

    # locked minutes per day, and within the late-night window.
    locked_total = work.groupby("date")["dur_min"].sum()
    ln_lo, ln_hi = config.LATE_NIGHT_WINDOW
    locked_late = _locked_minutes_in_window(work, ln_lo, ln_hi)

    # screen_time_min: a full day has 1440 locked-or-unlocked minutes; the unlocked
    # remainder is "on screen". Clip to a sane daily ceiling.
    screen_time = (1440.0 - locked_total).clip(lower=0.0, upper=900.0).rename("screen_time_min")
    window_min = (ln_hi - ln_lo) * 60.0
    late = (window_min - locked_late).clip(lower=0.0).rename("late_night_min")

    out = pd.concat([sleep, late, unlocks, screen_time], axis=1)
    out.index.name = "date"
    return out


def _locked_minutes_in_window(work: pd.DataFrame, hour_lo: int, hour_hi: int) -> pd.Series:
    """Per date, minutes of lock-interval overlap with [hour_lo, hour_hi) local."""
    rows = []
    for _, r in work.iterrows():
        s, e = r["start"], r["end"]
        for day in pd.date_range(s.normalize(), e.normalize(), freq="D"):
            w_start = day + pd.Timedelta(hours=hour_lo)
            w_end = day + pd.Timedelta(hours=hour_hi)
            ov = (min(e, w_end) - max(s, w_start)).total_seconds() / 60.0
            if ov > 0:
                rows.append((day.tz_localize(None), ov))
    if not rows:
        s = pd.Series(dtype="float64", name="locked_min")
        s.index.name = "date"
        return s
    g = pd.DataFrame(rows, columns=["date", "locked_min"]).groupby("date")["locked_min"].sum()
    g.index.name = "date"
    return g


# --- comms (sms + call_log): outgoing_msgs, unique_contacts ------------------------


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    return df[name] if name in df.columns else pd.Series(index=df.index, dtype="object")


def _comms_features(uid: str) -> pd.DataFrame:
    """outgoing_msgs (sent texts + outgoing calls) and unique_contacts per day."""
    cols = ["outgoing_msgs", "unique_contacts"]
    sms = _read_csv(config.DATASET_DIR / "sms" / f"sms_{uid}.csv")
    calls = _read_csv(config.DATASET_DIR / "call_log" / f"call_log_{uid}.csv")

    frames = []
    if not sms.empty and "timestamp" in sms.columns:
        ts = _to_local(sms["timestamp"])
        mtype = pd.to_numeric(_col(sms, "MESSAGES_type"), errors="coerce")
        frames.append(pd.DataFrame({
            "date": ts.dt.normalize().dt.tz_localize(None),
            "contact": _col(sms, "MESSAGES_address").astype(str),
            "outgoing": (mtype == 2).fillna(False),
        }))
    if not calls.empty and "timestamp" in calls.columns:
        ts = _to_local(calls["timestamp"])
        ctype = pd.to_numeric(_col(calls, "CALLS_type"), errors="coerce")
        frames.append(pd.DataFrame({
            "date": ts.dt.normalize().dt.tz_localize(None),
            "contact": _col(calls, "CALLS_number").astype(str),
            "outgoing": (ctype == 2).fillna(False),
        }))
    if not frames:
        return _empty(cols)

    ev = pd.concat(frames, ignore_index=True).dropna(subset=["date"])
    ev["contact"] = ev["contact"].replace({"nan": np.nan, "": np.nan})

    outgoing = ev[ev["outgoing"]].groupby("date").size().rename("outgoing_msgs")
    contacts = (ev.dropna(subset=["contact"]).groupby("date")["contact"]
                .nunique().rename("unique_contacts"))
    out = pd.concat([outgoing, contacts], axis=1)
    out.index.name = "date"
    return out


# --- gps: location_entropy, time_at_home_pct ---------------------------------------


def _gps_features(uid: str) -> pd.DataFrame:
    """location_entropy and time_at_home_pct per day from GPS fixes."""
    cols = ["location_entropy", "time_at_home_pct"]
    df = _read_csv(config.DATASET_DIR / "sensing" / "gps" / f"gps_{uid}.csv")
    if df.empty or not {"time", "latitude", "longitude"}.issubset(df.columns):
        return _empty(cols)

    ts = _to_local(df["time"])
    lat = pd.to_numeric(df["latitude"], errors="coerce").round(config.GPS_GRID_DECIMALS)
    lon = pd.to_numeric(df["longitude"], errors="coerce").round(config.GPS_GRID_DECIMALS)
    g = pd.DataFrame({
        "date": ts.dt.normalize().dt.tz_localize(None),
        "hour": ts.dt.hour,
        "cell": lat.astype("string") + "," + lon.astype("string"),
    }).dropna(subset=["date", "cell"])
    g = g[~g["cell"].str.contains("<NA>", na=True)]
    if g.empty:
        return _empty(cols)

    h_lo, h_hi = config.HOME_NIGHT_WINDOW
    night = g[(g["hour"] >= h_lo) & (g["hour"] < h_hi)]
    home_cell = (night["cell"].mode().iloc[0] if not night.empty else g["cell"].mode().iloc[0])

    entropy = g.groupby("date")["cell"].apply(_shannon_entropy).rename("location_entropy")
    home_pct = (g.assign(at_home=(g["cell"] == home_cell))
                .groupby("date")["at_home"].mean().rename("time_at_home_pct"))
    out = pd.concat([entropy, home_pct], axis=1)
    out.index.name = "date"
    return out


def _shannon_entropy(cells: pd.Series) -> float:
    counts = cells.value_counts().to_numpy(dtype="float64")
    if counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


# --- activity: steps proxy ---------------------------------------------------------


def _activity_features(uid: str) -> pd.DataFrame:
    """`steps` proxy: count of 'walking'/'running' activity inferences per day.

    StudentLife's activity inference codes: 0 stationary, 1 walking, 2 running,
    3 unknown. We scale active samples into a rough daily step-count band so the
    feature lives on the same scale as the contract fixtures (a few thousand).
    """
    cols = ["steps"]
    df = _read_csv(config.DATASET_DIR / "sensing" / "activity" / f"activity_{uid}.csv")
    if df.empty:
        return _empty(cols)
    tcol = "timestamp" if "timestamp" in df.columns else df.columns[0]
    acol = "activity inference" if "activity inference" in df.columns else df.columns[-1]

    ts = _to_local(df[tcol])
    act = pd.to_numeric(df[acol], errors="coerce")
    work = pd.DataFrame({
        "date": ts.dt.normalize().dt.tz_localize(None),
        "active": act.isin([1, 2]),
    }).dropna(subset=["date"])
    if work.empty:
        return _empty(cols)
    # ~ each active sample (sampled ~every few s, dutycycled) -> ~40 steps band.
    steps = (work.groupby("date")["active"].sum() * 40.0).clip(upper=20000.0).rename("steps")
    out = steps.to_frame()
    out.index.name = "date"
    return out


# --- public assembly ---------------------------------------------------------------


def build_user_features(uid: str) -> pd.DataFrame:
    """All FeatureRecord feature columns for one user, one row per day."""
    parts = [
        _phonelock_features(uid),
        _comms_features(uid),
        _gps_features(uid),
        _activity_features(uid),
    ]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=["user_id", "date", *FEATURE_NAMES])

    df = pd.concat(parts, axis=1)
    df = df[~df.index.isna()]
    df["dwell_flagged_min"] = 0.0  # not in datasets; injected by the demo simulator

    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = np.nan
    df = df.sort_index().reset_index().rename(columns={"index": "date"})
    df["user_id"] = uid
    return df[["user_id", "date", *FEATURE_NAMES]]
