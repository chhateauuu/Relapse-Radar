"""Train the fusion model + emit the AUC chart.   [P1]

TODO(P1):
  1. Load a public dataset (StudentLife first; then GLOBEM / CrossCheck).
  2. Build the personal baseline (per user+feature rolling median/IQR -> z-scores).
  3. Train LightGBM: z-score vector -> risk.
  4. Save the model to brain/models/ and plot ROC/AUC to brain/notebooks/.
"""
from __future__ import annotations


def main() -> None:
    print("TODO(P1): load data -> personal baseline -> train LightGBM -> AUC chart")


if __name__ == "__main__":
    main()
