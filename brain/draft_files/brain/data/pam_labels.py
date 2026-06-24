# brain/data/pam_labels.py
"""PAM (Photographic Affect Meter) EMA -> per-user-day affect labels.

PAM presents a 4x4 grid of 16 photos. picture_idx (1-16) encodes valence (columns,
increasing left->right) and arousal (rows). Following Pollak et al. (2011) and the
paper's Table 2, we derive:
  - `affect_neg`  : binary, 1 = negative valence (Relapse-Radar-relevant target)
  - `pam_class`   : 4-class quadrant (1 Neg/High, 2 Neg/Low, 3 Pos/Low, 4 Pos/High)

Multiple PAM responses in a day are averaged (valence & arousal) then re-quantized.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from brain import config


def _grid(idx: int) -> tuple[int, int]:
    """picture_idx (1-16) -> (valence 1-4 increasing right, arousal 1-4 increasing up)."""
    i = int(idx) - 1
    col = (i % 4) + 1            # valence: 1..4 left->right
    row = (i // 4) + 1          # 1=top .. 4=bottom
    arousal = 5 - row           # arousal increases upward (top row = high)
    return col, arousal


def _load_user_pam(uid: str) -> pd.DataFrame:
    path = config.DATASET_DIR / "EMA" / "response" / "PAM" / f"PAM_{uid}.json"
    if not path.exists():
        return pd.DataFrame()
    try:
        raw = json.loads(path.read_text())
    except Exception:
        return pd.DataFrame()
    rows = []
    for r in raw:
        idx = r.get("picture_idx")
        ts = r.get("resp_time")
        if idx is None or ts is None:
            continue
        val, aro = _grid(idx)
        rows.append({"resp_time": ts, "valence": val, "arousal": aro})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    dt = pd.to_datetime(df["resp_time"], unit="s", utc=True).dt.tz_convert(config.LOCAL_TZ)
    df["date"] = dt.dt.normalize().dt.tz_localize(None).dt.date
    df["user_id"] = uid
    return df


def load_pam_labels(users: list[str] | None = None) -> pd.DataFrame:
    """Per-user-day PAM labels: columns [user_id, date, valence, arousal, affect_neg, pam_class]."""
    pam_dir = config.DATASET_DIR / "EMA" / "response" / "PAM"
    if users is None:
        users = sorted({m.group(1) for p in pam_dir.glob("PAM_u*.json")
                        if (m := re.search(r"_(u\d+)\.json$", p.name))})

    frames = [d for uid in users if not (d := _load_user_pam(uid)).empty]
    if not frames:
        raise RuntimeError("No PAM responses found — check dataset path.")

    df = pd.concat(frames, ignore_index=True)
    daily = (
        df.groupby(["user_id", "date"])[["valence", "arousal"]]
        .mean()
        .reset_index()
    )
    pos_valence = daily["valence"] >= 2.5     # right half of the grid
    high_arousal = daily["arousal"] >= 2.5
    daily["affect_neg"] = (~pos_valence).astype(int)
    # 4-class quadrant matching the paper's Table 2.
    daily["pam_class"] = np.select(
        [
            (~pos_valence) & high_arousal,   # 1 Negative / High  (stress)
            (~pos_valence) & ~high_arousal,  # 2 Negative / Low   (depressive)
            pos_valence & ~high_arousal,     # 3 Positive / Low   (calm)
            pos_valence & high_arousal,      # 4 Positive / High  (energy)
        ],
        [1, 2, 3, 4],
        default=0,
    )
    return daily
