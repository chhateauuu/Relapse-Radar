# brain/config.py
"""Central config: paths, constants, and the single missing-data rule."""
from __future__ import annotations

from pathlib import Path

# --- Paths ---
REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO_ROOT / "dataset" / "studentlife"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"

# StudentLife was run at Dartmouth (US Eastern). Epoch timestamps are UTC.
LOCAL_TZ = "America/New_York"

# --- Feature-extraction windows ---
NIGHT_SLEEP_WINDOW = (21, 11)     # 21:00 -> 11:00 next day, search window for the main sleep gap
LATE_NIGHT_WINDOW = (1, 5)        # 01:00 - 05:00 local, "late night use"
HOME_NIGHT_WINDOW = (0, 6)        # 00:00 - 06:00 used to infer each user's home location
GPS_GRID_DECIMALS = 3             # ~110 m grid for location clustering

# --- Label rule (PHQ-9) ---
# PHQ-9: 9 symptom items, each 0-3. Total 0-27. >= 10 == moderate+ depression.
PHQ9_RESPONSE_MAP = {
    "not at all": 0,
    "several days": 1,
    "more than half the days": 2,
    "nearly every day": 3,
}
PHQ9_CUTOFF = 10                  # >= cutoff -> positive label
PHQ9_PREFER = "post"             # use post-study survey, fall back to pre

# --- Missing-data rule (single source of truth) ---
# 1. Forward-fill then back-fill each feature WITHIN a user (time-ordered).
# 2. Any value still missing -> fill with that user's median, else the global median.
# 3. Drop a user-day if > MAX_MISSING_FRAC of features were missing before fill.
MAX_MISSING_FRAC = 0.5

# Minimum user-days required to keep a user (need history for personal baselines).
MIN_USER_DAYS = 5

# --- Model / split ---
RANDOM_SEED = 42
N_SPLITS = 5                      # GroupKFold folds (group = user_id)
