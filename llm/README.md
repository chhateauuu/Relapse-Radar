# llm/ — explanation + check-in (P3)

The empathy layer. Turns the brain's `drivers` into a human sentence, and runs the HALT check-in. **Not the predictor** — that's the brain.

- `explain(assessment) -> str`
- `checkin() -> str`

Keep keys in `.env` (gitignored). On-device (Ollama) is the privacy-story prod path; an API call is fine for the demo.

Run: `python llm/llm.py`
