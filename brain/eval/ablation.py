"""Personal-baseline vs population ablation — the proof chart.   [P2]

The single most important "is this real AI?" artifact. It shows that scoring
each person against THEIR OWN baseline (per-user z-scores) beats a population
model on raw features at flagging spiral days — i.e. *individualized AI, not an
if-statement*.

Why personal wins: people's "normal" differs a lot. On RAW features a naturally
poor-sleeper's good day can look like a good-sleeper's bad night, so a
population model is confused by cross-person variance. Per-user z-scores remove
that variance, exposing each person's own drift.

This runs on a SYNTHETIC cohort (clean + reproducible, isolates the one
variable). Swap in P1's real StudentLife/CrossCheck model + `to_zscores()` for
the honest real-data panel — same two-bar comparison.

Run:  python brain/eval/ablation.py        (writes brain/eval/ablation.png)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from simulator.simulator import BASELINE

SIGNALS = list(BASELINE.keys())

# Risk-increasing direction per signal (mirrors brain.eval.drivers).
RISK_DIRECTION = {
    "sleep_hours": "down", "late_night_min": "up", "screen_time_min": "up",
    "unlocks": "up", "outgoing_msgs": "down", "unique_contacts": "down",
    "location_entropy": "down", "time_at_home_pct": "up",
    "dwell_flagged_min": "up", "steps": "down",
}

# Cohort knobs (as fractions of each signal's population mean). The spiral is
# deliberately SUBTLE vs the cross-person spread — that's the regime where
# personalization actually matters (and where real relapse signals live).
CROSS_USER_SD = 0.22    # how much people differ from each other (big)
WITHIN_USER_SD = 0.06   # a person's day-to-day wobble (small)
SPIRAL_SHIFT = 0.16     # how far a spiral pushes a signal (modest)


def make_cohort(
    n_users: int = 80,
    healthy_days: int = 45,
    spiral_days: int = 7,
    spiral_frac: float = 0.5,
    seed: int = 42,
) -> pd.DataFrame:
    """A heterogeneous cohort of user-days labeled healthy (0) / spiral (1)."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    n_spiralers = int(round(n_users * spiral_frac))

    for u in range(n_users):
        # This user's personal normal (differs across people).
        base = {s: max(BASELINE[s] * (1 + CROSS_USER_SD * rng.standard_normal()), 1e-3)
                for s in SIGNALS}
        is_spiraler = u < n_spiralers

        for _ in range(healthy_days):
            feats = {s: base[s] * (1 + WITHIN_USER_SD * rng.standard_normal()) for s in SIGNALS}
            rows.append({"user": u, "label": 0, **feats})

        if is_spiraler:
            for i in range(spiral_days):
                t = (i + 1) / spiral_days
                e = 0.4 * t + 0.6 * t * t  # accelerating, same easing as the sim
                feats = {}
                for s in SIGNALS:
                    sign = 1.0 if RISK_DIRECTION[s] == "up" else -1.0
                    shift = sign * SPIRAL_SHIFT * BASELINE[s] * e
                    feats[s] = base[s] + shift + base[s] * WITHIN_USER_SD * rng.standard_normal()
                rows.append({"user": u, "label": 1, **feats})

    return pd.DataFrame(rows)


def personal_z(df: pd.DataFrame) -> pd.DataFrame:
    """Per-user z-scores vs each user's OWN healthy-day median/IQR.

    Self-normalization that's available on-device at inference (the user's own
    history) — exactly the personal baseline P1 will expose as `to_zscores()`.
    """
    out = df.copy()
    for _, g in df.groupby("user"):
        healthy = g[g["label"] == 0]
        for s in SIGNALS:
            med = healthy[s].median()
            iqr = healthy[s].quantile(0.75) - healthy[s].quantile(0.25)
            scale = iqr if iqr > 1e-6 else (healthy[s].std() or 1.0)
            out.loc[g.index, s] = (g[s] - med) / scale
    return out


def _oof_auc(X: np.ndarray, y: np.ndarray, groups: np.ndarray, seed: int = 42) -> float:
    """Honest AUC: GroupKFold by user (test users never seen in training)."""
    import warnings

    from lightgbm import LGBMClassifier

    oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        clf = LGBMClassifier(
            n_estimators=200, learning_rate=0.05, num_leaves=15,
            subsample=0.8, colsample_bytree=0.8, random_state=seed, verbosity=-1,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            clf.fit(X[tr], y[tr])
            oof[te] = clf.predict_proba(X[te])[:, 1]
    return float(roc_auc_score(y, oof))


def run_ablation(seed: int = 42) -> dict:
    """Compute population-vs-personal AUC on the synthetic cohort."""
    df = make_cohort(seed=seed)
    y = df["label"].to_numpy()
    groups = df["user"].to_numpy()

    auc_pop = _oof_auc(df[SIGNALS].to_numpy(), y, groups, seed)
    auc_per = _oof_auc(personal_z(df)[SIGNALS].to_numpy(), y, groups, seed)

    return {
        "population": auc_pop,
        "personal": auc_per,
        "lift": auc_per - auc_pop,
        "n_users": int(df["user"].nunique()),
        "n_days": int(len(df)),
        "positive_rate": float(y.mean()),
    }


def plot(result: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["Population\n(raw features)", "Personal\n(per-user z-scores)"]
    vals = [result["population"], result["personal"]]
    colors = ["#9aa0a6", "#1a73e8"]

    fig, ax = plt.subplots(figsize=(5.6, 4.3))
    bars = ax.bar(labels, vals, color=colors, width=0.6)
    ax.axhline(0.5, ls="--", lw=1, color="#bbb", label="chance")
    ax.set_ylim(0.5, 1.0)
    ax.set_ylabel("AUC (honest, GroupKFold by user)")
    ax.set_title("Personal baseline beats population\nat flagging spiral days")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.3f}",
                ha="center", va="bottom", fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.text(0.5, 0.015,
             f"+{result['lift']:.3f} AUC from personalization  ·  "
             f"synthetic cohort, n={result['n_users']} users",
             ha="center", fontsize=8.5, color="#1a73e8")
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    import json

    result = run_ablation()
    print(json.dumps(result, indent=2))

    out = Path(__file__).resolve().parent / "ablation.png"
    plot(result, out)
    print("chart ->", out)

    assert result["personal"] > result["population"], result
    print(f"OK: personal {result['personal']:.3f} > population {result['population']:.3f} "
          f"(+{result['lift']:.3f})")
