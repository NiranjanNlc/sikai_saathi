"""Fireworks AI tutoring client (OpenAI-compatible inference).

Model ID must be verified from the current Fireworks catalog and set via
FIREWORKS_MODEL_ID. Without a key/model the orchestrator falls back to mock.
"""

import httpx

SYSTEM_PROMPT = (
    "You are Sikāi Sathi, a kind maths tutor for a Grade 8 student in Nepal. "
    "RULES:\n"
    "1. Reply ONLY in the requested language. For Nepali use simple Devanagari and "
    "always the informal 'तिमी' form (never 'तपाईं'). Keep numbers and symbols as digits.\n"
    "2. Write maths as PLAIN TEXT like 3x + 5 = 20. Never use backticks, $...$, LaTeX or markdown.\n"
    "3. Be brief: at most 5 short sentences, then exactly ONE guiding question as the last line.\n"
    "4. Use the balance-scale idea: whatever you do to one side, do to the other.\n"
    "5. Name what the student did RIGHT first, then the specific mistake from the diagnosis "
    "using the real numbers of THIS problem.\n"
    "6. Do not reveal the final answer x = ... unless the student asked for the steps; "
    "if they asked for steps, list the steps (one per line) using the real numbers.\n"
    "7. Finish the last question completely. Never leave a sentence unfinished."
)

MISCONCEPTION_HINTS = {
    "forgot_to_divide": "The student subtracted the constant correctly but stopped before dividing by the coefficient of x.",
    "one_sided_operation": "The student changed only one side of the equation.",
    "sign_error": "The student used the wrong sign when moving a term across '='.",
    "correct": "The student's work is correct; praise it and suggest a harder try.",
    "unclear": "The diagnosis is unclear; ask the student to explain their last step.",
}


class FireworksTutorProvider:
    name = "fireworks"

    def __init__(self, *, api_key: str, model_id: str,
                 timeout_s: float = 60.0) -> None:
        if not api_key:
            raise ValueError("FIREWORKS_API_KEY is required for the Fireworks provider")
        if not model_id:
            raise ValueError("FIREWORKS_MODEL_ID must be verified from the catalog")
        self._api_key = api_key
        self._model_id = model_id
        self._timeout = timeout_s

    def explain(self, *, misconception: str, context: str, language: str,
                problem_text: str = "") -> dict:
        lang_name = "Nepali" if language == "ne" else "English"
        payload = {
            "model": self._model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Problem: {problem_text or '(not given)'}\n"
                    f"Diagnosed misconception: {misconception} - "
                    f"{MISCONCEPTION_HINTS.get(misconception, '')}\n"
                    f"Student's work / question: {context or '(none)'}\n"
                    f"Language: {lang_name}\n"
                    "Give a short explanation plus one follow-up question."
                )},
            ],
            "max_tokens": 3000,  # reasoning models spend tokens thinking first
            "temperature": 0.4,
            "reasoning_effort": "minimal",  # keeps latency classroom-friendly
        }
        text = ""
        last_exc: Exception | None = None
        for _attempt in range(3):
            try:
                resp = httpx.post(
                    "https://api.fireworks.ai/inference/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                    timeout=self._timeout,
                )
                if resp.status_code >= 500:
                    last_exc = RuntimeError(f"HTTP {resp.status_code}")
                    continue
                resp.raise_for_status()
                text = (resp.json()["choices"][0]["message"].get("content") or "").strip()
                break
            except (httpx.HTTPError, KeyError) as exc:
                raise ProviderError(f"Fireworks request failed: {exc}") from exc
        else:
            raise ProviderError(f"Fireworks request failed: {last_exc}")
        if not text:
            raise ProviderError("Fireworks returned an empty answer")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        followup = lines[-1] if len(lines) > 1 else ""
        return {"explanation": text.strip(), "followup_question": followup}


class ProviderError(RuntimeError):
    pass
