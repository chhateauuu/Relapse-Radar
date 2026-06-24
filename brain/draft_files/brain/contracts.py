# brain/contracts.py
"""The two FROZEN contracts shared with P2/P3/P4. Do not change without telling the team."""
from dataclasses import dataclass, field
from datetime import date as Date
from typing import Optional

# Canonical ordered list of model feature names (raw passive-sensing fields).
FEATURE_NAMES: list[str] = [
    "sleep_hours",
    "late_night_use_min",
    "outgoing_comms",
    "unique_contacts",
    "location_entropy",
    "time_at_home_frac",
    "screen_unlocks",
    "near_flagged_min",
]


# --- Input: one user, one day, all features. P1 produces these from datasets. ---
@dataclass
class FeatureRecord:
    user_id: str
    date: Date
    sleep_hours: float            # overnight inactivity proxy
    late_night_use_min: float     # screen events 1-5am, minutes
    outgoing_comms: int           # texts + calls count (metadata only)
    unique_contacts: int          # distinct people contacted
    location_entropy: float       # mobility / distinct-places measure
    time_at_home_frac: float      # 0-1, fraction of day at home
    screen_unlocks: int           # unlock count
    near_flagged_min: float = 0.0 # geofence dwell; 0 in datasets, used in demo
    label: Optional[int] = None   # 1 = adverse outcome (relapse/depression flag), else 0/None


# --- Output: P1 fills `risk` + `drivers`; P2 fills `state`. ---
@dataclass
class RiskAssessment:
    user_id: str
    date: Date
    risk: float                   # 0-1, from P1's LightGBM model
    drivers: list[str] = field(default_factory=list)  # top contributing signals (SHAP), P1
    state: str = "GREEN"          # GREEN | AMBER | RED — P2 fills via change-point
    started_days_ago: Optional[int] = None            # P2 fills


# --- The function everyone imports ---
def assess(record: FeatureRecord) -> RiskAssessment:  # pragma: no cover - real impl in assess.py
    """Frozen signature. Real implementation lives in top-level assess.py."""
    raise NotImplementedError("Import assess() from assess.py")
