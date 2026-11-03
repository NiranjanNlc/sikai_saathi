"""Meta Muse Spark client via the Model API (OpenAI-compatible chat).

Docs to verify before production use: official Model API overview for
https://api.meta.ai/v1. Without MODEL_API_KEY the orchestrator falls
back to the mock provider instead of fabricating output.
"""

import json

import httpx

SYSTEM_PROMPT = (
    "You analyze a Grade 8 student's handwritten solution to a linear equation. "
    "Return ONLY valid JSON with keys: detected_steps (list of strings), "
    "suspected_misconception (one of: one_sided_operation, forgot_to_divide, "
    "sign_error, correct, unclear), evidence (string), confidence (0..1), "
    "explanation (one short paragraph, simple Grade 8 language)."
)


class SparkDiagnoseProvider:
    name = "spark"

    def __init__(self, *, api_key: str, base_url: str,
                 model_id: str = "muse-spark-1.3",
                 timeout_s: float = 60.0) -> None:
        if not api_key:
            raise ValueError("MODEL_API_KEY is required for the Spark provider")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_id = model_id
        self._timeout = timeout_s

    def diagnose(self, *, problem_text: str, image_base64: str | None,
                 steps_text: str | None, language: str) -> dict:
        content: list[dict] = [
            {"type": "text",
             "text": f"Problem: {problem_text}\nStudent steps (if transcribed): {steps_text or '(none)'}\n"
                     f"Reply language: {'Nepali' if language == 'ne' else 'English'}."}
        ]
        if image_base64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            })
        payload = {
            "model": self._model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
        }
        try:
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Spark request failed: {exc}") from exc
        return {
            "detected_steps": list(data.get("detected_steps", [])),
            "suspected_misconception": str(data.get("suspected_misconception", "unclear")),
            "evidence": str(data.get("evidence", "")),
            "confidence": float(data.get("confidence", 0.0)),
            "explanation": str(data.get("explanation", "")),
        }


class ProviderError(RuntimeError):
    pass
