# brain/data/fixtures.py
"""Fake records + a stub assess() so P2/P3/P4 can build against the interface immediately."""
from __future__ import annotations

from datetime import date

from brain.contracts import FeatureRecord, RiskAssessment


def sample_records() -> list[FeatureRecord]:
    """A few hand-made records spanning low/medium/high risk-looking behavior."""
    return [
        # Looks healthy: good sleep, social, mobile.
        FeatureRecord(
            user_id="demo_low",
            date=date(2013, 4, 1),
            sleep_hours=7.8,
            late_night_use_min=4.0,
            outgoing_comms=22,
            unique_contacts=9,
            location_entropy=1.9,
            time_at_home_frac=0.42,
            screen_unlocks=68,
            label=0,
        ),
        # Drifting: short sleep, more late-night use, fewer contacts.
        FeatureRecord(
            user_id="demo_mid",
            date=date(2013, 4, 2),
            sleep_hours=5.4,
            late_night_use_min=38.0,
            outgoing_comms=6,
            unique_contacts=3,
            location_entropy=0.9,
            time_at_home_frac=0.78,
            screen_unlocks=120,
            label=0,
        ),
        # Withdrawn: poor sleep, isolated, stuck at home.
        FeatureRecord(
            user_id="demo_high",
            date=date(2013, 4, 3),
            sleep_hours=3.9,
            late_night_use_min=92.0,
            outgoing_comms=1,
            unique_contacts=1,
            location_entropy=0.2,
            time_at_home_frac=0.97,
            screen_unlocks=180,
            label=1,
        ),
    ]


def stub_assess(record: FeatureRecord) -> RiskAssessment:
    """Deterministic dummy assess() — same signature as the real one. No model needed."""
    risk = 0.5
    drivers: list[str] = []
    if record.sleep_hours < 5.5:
        risk += 0.2
        drivers.append("low sleep_hours")
    if record.unique_contacts <= 3:
        risk += 0.15
        drivers.append("social withdrawal")
    if record.late_night_use_min > 30:
        risk += 0.1
        drivers.append("late_night_use_min high")
    risk = max(0.0, min(1.0, risk))
    return RiskAssessment(user_id=record.user_id, date=record.date, risk=risk, drivers=drivers[:3])
