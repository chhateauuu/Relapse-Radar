# brain/config.py
"""Central config for the P1 brain: dataset path, label rule, feature constants.

The dataset path can be overridden with the RELAPSE_DATASET_DIR env var so the
loaders work on any machine without editing code.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Paths ---
REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "brain" / "models"
NOTEBOOKS_DIR = REPO_ROOT / "brain" / "notebooks"

# StudentLife dataset root. Override with RELAPSE_DATASET_DIR if it lives elsewhere.
_DEFAULT_DATASET = Path(r"C:\Hackathon26\dataset\studentlife")
DATASET_DIR = Path(os.getenv("RELAPSE_DATASET_DIR", str(_DEFAULT_DATASET)))

# StudentLife was run at Dartmouth (US Eastern). Epoch timestamps are UTC.
LOCAL_TZ = "America/New_York"

# --- Feature-extraction windows ---
NIGHT_SLEEP_WINDOW = (21, 11)     # 21:00 -> 11:00 next day: search window for the sleep gap
LATE_NIGHT_WINDOW = (1, 5)        # 01:00 - 05:00 local, "late night use"
HOME_NIGHT_WINDOW = (0, 6)        # 00:00 - 06:00 used to infer each user's home location
GPS_GRID_DECIMALS = 3             # ~110 m grid for location clustering

# --- Label rule (PHQ-9) ---
# PHQ-9: 9 items, each 0-3 (total 0-27). >= 10 == moderate-or-worse depression.
PHQ9_RESPONSE_MAP = {
    "not at all": 0,
    "several days": 1,
    "more than half the days": 2,
    "nearly every day": 3,
}
PHQ9_CUTOFF = 10                  # >= cutoff -> positive label
PHQ9_PREFER = "post"              # prefer post-study survey, fall back to pre

# --- Missing-data rule ---
MAX_MISSING_FRAC = 0.5            # drop a user-day if > this fraction of features missing
MIN_USER_DAYS = 5                 # need this much history to keep a user

# --- Model / split ---
RANDOM_SEED = 42
N_SPLITS = 5                      # GroupKFold folds (group = user_id)
