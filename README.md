# Sikāi Sathi · सिकाइ साथी

Nepal-first AI learning companion for Grade 8 mathematics. Demo slice: linear equations.

> Your learning companion. Your language. Your pace.

**One-liner:** A Nepal-first AI companion that reads a Grade 8 student's handwritten math, names the exact mistake, explains it in Nepali, and proves learning with practice — never rote answers.

## Problem

1. **Rote over understanding.** Students memorize final answers (e.g. `x = 15`) instead of learning the step they missed (dividing both sides by 3).
2. **No 1:1 feedback at scale.** Teachers can't hand-mark every copy; parents can't always help with algebra.
3. **Language gap.** Most AI tutors explain in English. A Nepali-medium student thinks in Nepali (पक्ष, भाग गर) but is tested in a second language.
4. **Phone-first, low-bandwidth reality.** The student device is a low-to-mid Android phone on patchy 3G/4G — heavy apps and full-photo uploads fail.
5. **Untrustworthy AI.** Generic LLM tutors hallucinate correctness and invent mastery. In education, a wrong "Mastery: YES" is worse than no feedback.

## Solution

**Submit → Diagnose → Learn → Practice** — one learning loop, 4 screens, 3 taps to practice.

| Step | Student does | App does |
|---|---|---|
| 1. Submit | Photo of copy or typed steps | Pinned equation bar; Photo/Type tabs, "Try an example" |
| 2. Diagnose | Reads flagged steps | Highlights wrong line, names misconception in student language ("Look at line 3…", लाइन 3 हेर) |
| 3. Learn | Reads + answers inline | Nepali/English explanation, quick-check with self-check, balance-scale visual tipped by *their own* answer |
| 4. Practice | Solves fresh variant | Deterministic new question every time, hint → retry (2 tries) → worked solution, "N of 3" progress + activity timeline |

Core rule: **correctness, misconception labels, and mastery are decided only by deterministic Python (`backend/app/math_engine.py`). The LLM only explains.** Typed steps are diagnosed deterministically even when an LLM provider is active.

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

## Tech stack

- **Backend:** FastAPI + SQLite (`sikai.db`), seeded problems, `/api/diagnose`, `/api/tutor`, `/api/practice`, `/api/assessment`, `/api/progress`.
- **Deterministic core:** `math_engine.py` — solve, check, error classification (`forgot_to_divide`, `divided_only_c`, `sign_error`, `arithmetic_error`), similar-problem generator, balance-scale frames.
- **AI providers:** Muse Spark for image understanding/diagnosis; Fireworks-hosted Meta open-weight model for the tutoring route; mock providers with honest labels when keys are absent.
- **Frontend:** single `frontend/index.html` (Noto Sans Devanagari via Google Fonts), full EN/NE switch, `?debug` teacher view.

## Built with Meta

- **Muse Spark (Meta Model API)** reads the student's handwritten solution and returns structured diagnosis: transcribed steps, suspected misconception, evidence, and confidence (`backend/app/providers/spark.py`).
- **Meta open-weight models via Fireworks AI** generate the Socratic Nepali/English explanations behind the Learn step (`backend/app/providers/fireworks.py`).
- The app itself was built end-to-end in **Muse Code (powered by Muse Spark)**, which also acted as **senior UI/UX designer**: auditing the interface and drafting the redesign (navy/learning-blue brand system, benefit-led hero with a real product visual, full EN/NE localisation) so the product reads as a deliberate EdTech brand, not generic AI-generated UI.
- Meta's models only ever *explain* — correctness, misconception labels, and mastery are decided solely by deterministic Python (see Rules below).

## Rules the code enforces

- Mathematical correctness, misconception labels and mastery are decided only by `backend/app/math_engine.py` — typed steps are diagnosed deterministically even when an LLM provider is active.
- Mastery requires **3 correct practice answers in a row**, never the demo itself; the result screen always shows this attempt and overall progress separately.
- Keys live on the backend; the frontend never sees them.
- Provider failures fall back to mock with a visible banner — never fabricated model output.
- No claim of official Nepal curriculum alignment without verified curriculum data.
- Every UI string ships in English + Nepali (`STR` table in `frontend/index.html`); dev details (provider, confidence) appear only with `?debug`.

## Roadmap

- **Phase 1 (done for demo):** deterministic diagnosis for supported errors, hint → retry loop, full localisation, 4-screen flow, honest fallback states.
- **Phase 2 (next):** think-aloud tests with 5–6 Grade 7–10 students on their own phones + teacher review; fix register (तपाईं vs तिमी) and visual polish.
- **Phase 3 (after hackathon):** history/teacher view from `/api/progress`, PWA offline shell, more linear-equation error types — then expand beyond Grade 8 equations. Explicitly out of scope: full LMS, teacher dashboard, voice, complete SEE curriculum.

## Tests and eval

```bash
uv run pytest -q
uv run python scripts/eval_language.py            # mock structure check
uv run python scripts/eval_language.py --provider fireworks   # needs key; human-grade Nepali
```

## License

MIT — see [LICENSE](LICENSE).
