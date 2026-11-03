# Sikāi Sathi · सिकाइ साथी

Nepal-first AI learning companion for Grade 8 mathematics. Demo slice: linear equations.

> Your learning companion. Your language. Your pace.

## Quick start

```bash
cp .env.example .env   # then fill in keys (auto-loaded)
export PATH="$HOME/.local/bin:$PATH"   # if uv was just installed
uv venv
uv pip install -e ".[test]"
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Health + active providers |
| GET | `/api/problems` | Seeded problems |
| POST | `/api/diagnose` | Analyze handwritten work (image or typed steps) |
| POST | `/api/tutor` | Socratic explanation in Nepali/English |
| GET | `/api/practice/{problem_id}?index=1` | Deterministic practice variant |
| POST | `/api/assessment` | Deterministic answer check + mastery |
| GET | `/api/progress/{student_id}` | Learning evidence |

## Configuration (.env)

- `DIAGNOSE_PROVIDER=mock|spark`, `TUTOR_PROVIDER=mock|fireworks`
- `MODEL_API_KEY`, `MODEL_BASE_URL` (default `https://api.meta.ai/v1`)
- `FIREWORKS_API_KEY`, `FIREWORKS_MODEL_ID` (verify from the Fireworks catalog)
- `DATABASE_PATH` (default `sikai.db`)

Without keys the app runs on mock providers and labels them honestly in the UI.

## Rules the code enforces

- Mathematical correctness, misconception labels and mastery are decided only by `backend/app/math_engine.py` — typed steps are diagnosed deterministically even when an LLM provider is active.
- Mastery requires **3 correct practice answers in a row**, never the demo itself; the result screen always shows this attempt and overall progress separately.
- Keys live on the backend; the frontend never sees them.
- Provider failures fall back to mock with a visible banner — never fabricated model output.
- Every UI string ships in English + Nepali (`STR` table in `frontend/index.html`); dev details (provider, confidence) appear only with `?debug`.

## Tests and eval

```bash
uv run pytest -q
uv run python scripts/eval_language.py            # mock structure check
uv run python scripts/eval_language.py --provider fireworks   # needs key; human-grade Nepali
```

See [DEMO.md](DEMO.md) for the demo script.
