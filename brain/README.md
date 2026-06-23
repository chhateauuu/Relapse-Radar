# brain/ — the ML core (P1 + P2)

Clean file split so the two of you never collide:

| Path | Owner | Purpose |
|---|---|---|
| `data/` | P1 | dataset loaders (StudentLife / GLOBEM / CrossCheck) -> FeatureRecord tables |
| `models/` | P1 | saved model + baseline (gitignored binaries) |
| `train.py` | P1 | trains, saves, emits the **AUC** chart |
| `assess.py` | P1 + P2 | `assess(FeatureRecord) -> RiskAssessment` (P1 risk; calls P2 for state/drivers) |
| `eval/` | P2 | change-point/state detector, SHAP drivers, **personal-vs-population ablation** |
| `notebooks/` | P1 + P2 | AUC + ablation charts |

**Contract:** honor `../shared/contracts.md` exactly. **Start:** P1 on data+model, P2 on the simulator (`../simulator/`) + change-point. P2's SHAP + ablation wait on P1's trained model — mock with synthetic until then.

Run: `python -m brain.train`
