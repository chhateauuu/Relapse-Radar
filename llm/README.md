# llm/ — explanation + check-in (P3)

The empathy/interface layer. Turns the brain's `drivers` into a human sentence
and runs the HALT check-in. **Not the predictor** — that's the brain.

- `explain(assessment) -> str` — top drivers → a kind, non-clinical sentence.
- `checkin() -> str` — a short HALT (Hungry/Angry/Lonely/Tired) nudge.

With `OPENAI_API_KEY` set it calls a real model; otherwise it composes the
sentence locally from the drivers (fully offline). On-device Ollama is the
privacy-story prod path. Keys live in `.env` (gitignored) — see `.env.example`.

The API calls `explain()` to fill `RiskAssessment.explanation` on `/assess` and
`/simulate/step`, and exposes `checkin()` at `GET /checkin`.

Run standalone: `python llm/llm.py`
