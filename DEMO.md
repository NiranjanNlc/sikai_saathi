# Demo script — Sikāi Sathi (5 minutes)

Setup: server running on port 8000, browser open on `/`, language Nepali.

## 1. Submit (30s)
Show Screen 1. Pick the **Type steps** tab, press **Try an example**:
`3x + 5 = 20 → 3x = 15 → x = 15`. Click **Check my steps**.

Say: “The student did the subtraction but stopped before dividing.”

## 2. Diagnosis (1 min)
Screen 2: detected steps with the wrong line flagged, student-language
evidence (“Look at line 3…”), growth-tone message. Note the pinned
equation bar and the clickable stepper.
Append `?debug` to show provider + confidence (teacher view).

## 3. Learn (1.5 min)
Screen 3: Nepali explanation, inline quick-check with self-check feedback,
then the balance visual — the student's own answer tips the scale first.
Key line: “Whatever you do to one side, do the same to the other.”

## 4. Practice (1.5 min)
Screen 4: a fresh deterministic question (rotates every time).
Answer it wrong once to show the hint + retry (answer stays hidden).
Miss twice to show the worked solution, then take a new question.
Answer correctly: this try vs overall “N of 3” progress stay separate —
mastery needs 3 in a row and never contradicts the result above it.

## 5. Evidence (30s)
Same screen: progress counts + recent-activity timeline.
Mention: correctness is Python, not LLM vibes.

## Fallback beats (if asked)
- Kill the provider (unset key / pick spark without key): banner + mock-fallback tag.
- Switch language to English: every string switches, including diagnosis and result.
- Type `hello` as steps: honest “I couldn't read that” state with a retake.
- Mismatched steps (demo steps under problem 2x + 7 = 15): mismatch warning.
- Numeral toggle in the header: 123 / १२३.
