"""Mock providers for tests, demos without keys, and fallback states.

Never fabricate real model output: responses are clearly derived from
deterministic mock rules and labelled with provider='mock'. All text is
built from the actual problem numbers (nothing is hard-coded to one problem).
"""

import re

from .. import seed as seed_module
from ..math_engine import (
    LinearProblem, diagnose_steps, diagnosis_evidence, fmt,
)

_MISC_CONFIDENCE = {
    "correct": 0.95,
    "forgot_to_divide": 0.9,
    "sign_error": 0.9,
    "one_sided_operation": 0.9,
    "arithmetic_error": 0.7,
    "unclear": 0.3,
}


def _find_problem(problem_text: str) -> LinearProblem | None:
    for p in seed_module.SEED_PROBLEMS:
        if p.text == problem_text:
            return p
    m = re.fullmatch(r"\s*(\d+)x\s*([+-])\s*(\d+)\s*=\s*(-?\d+)\s*", problem_text or "")
    if m:
        a, sign, b, c = int(m[1]), m[2], int(m[3]), int(m[4])
        return LinearProblem("adhoc", a, b if sign == "+" else -b, c, problem_text)
    return None


def _move(problem: LinearProblem | None) -> tuple[str, str, str, str]:
    """(en_first_move, ne_first_move, en_last_move, ne_last_move)."""
    if problem is None:
        return ("do the same operation on both sides", "दुवै पक्षमा एउटै क्रिया गर्नुहोस्",
                "divide both sides by the coefficient of x",
                "दुवै पक्षलाई x को गुणाङ्कले भाग गर्नुहोस्")
    b, a = problem.b, problem.a
    en1 = (f"subtract {fmt(b)} from both sides" if b > 0
           else f"add {fmt(abs(b))} to both sides" if b < 0 else "keep both sides balanced")
    ne1 = (f"दुवै पक्षबाट {fmt(b)} घटाउनुहोस्" if b > 0
           else f"दुवै पक्षमा {fmt(abs(b))} जोड्नुहोस्" if b < 0 else "दुवै पक्षलाई सन्तुलित राख्नुहोस्")
    return (en1, ne1, f"divide both sides by {fmt(a)}", f"दुवै पक्षलाई {fmt(a)} ले भाग गर्नुहोस्")


def explanation_for(misconception: str, lang: str, problem: LinearProblem | None) -> str:
    en1, ne1, en2, ne2 = _move(problem)
    mid = ""
    if problem is not None:
        mid = fmt(problem.c - problem.b)
        coef = fmt(problem.a)
    if misconception == "one_sided_operation":
        return ("You changed one side of the equation but not the other. "
                "Whatever you do to one side, do the same to the other side."
                if lang == "en" else
                "तिमीले समीकरणको एउटा पक्ष मात्र परिवर्तन गर्यौ। "
                "एउटा पक्षमा जे गर्छौ, अर्को पक्षमा पनि त्यही गर्नुपर्छ।")
    if misconception == "forgot_to_divide" and problem is not None:
        return (f"You did the first step correctly, but stopped early. After {coef}x = {mid}, "
                f"you still need to {en2}."
                if lang == "en" else
                f"पहिलो चरण तिमीले सही गर्यौ, तर बीचमै रोकियौ। {coef}x = {mid} पछि "
                f"{ne2}।")
    if misconception == "sign_error":
        return ("Check the sign when moving a term across '='. Use the opposite operation "
                "on both sides." if lang == "en" else
                "'=' पार गर्दा चिन्ह जाँच। दुवै पक्षमा उल्टो क्रिया प्रयोग गर।")
    if misconception == "correct":
        return ("Your steps look correct. Each operation was applied to both sides."
                if lang == "en" else
                "तिमीका चरणहरू सही देखिन्छन्। हरेक क्रिया दुवै पक्षमा लागू भएको छ।")
    return (f"I could not tell what went wrong, so here is the safe path: {en1}, then {en2}."
            if lang == "en" else
            f"के गल्ती भयो थाहा भएन, त्यसैले सुरक्षित बाटो: {ne1}, त्यसपछि {ne2}।")


class MockDiagnoseProvider:
    name = "mock"

    def diagnose(self, *, problem_text: str, image_base64: str | None,
                 steps_text: str | None, language: str) -> dict:
        lang = language if language in ("ne", "en") else "en"
        problem = _find_problem(problem_text)
        steps = [s.strip() for s in (steps_text or "").splitlines() if s.strip()]

        if steps and problem is not None:
            det = diagnose_steps(problem, steps)
            misconception = det["misconception"]
            evidence = diagnosis_evidence(problem, det, lang)
            error_step_index: int | None = det["error_step_index"]
            problem_mismatch: bool = det["problem_mismatch"]
        elif image_base64 and problem is not None:
            steps = [problem_text]
            misconception = "unclear"
            evidence = ("Mock cannot read handwriting; type your steps for a real check."
                        if lang == "en" else
                        "मकले हस्तलेखन पढ्न सक्दैन; वास्तविक जाँचका लागि चरणहरू टाइप गर।")
            error_step_index, problem_mismatch = None, False
        else:
            steps = [problem_text] if problem is not None else []
            misconception = "unclear"
            det = {"misconception": "unclear", "detail": "unreadable"}
            evidence = (diagnosis_evidence(problem, det, lang)
                        if problem is not None else
                        "I couldn't read those steps.")
            error_step_index, problem_mismatch = None, False

        return {
            "detected_steps": steps,
            "suspected_misconception": misconception,
            "evidence": evidence,
            "confidence": _MISC_CONFIDENCE.get(misconception, 0.3),
            "explanation": explanation_for(misconception, lang, problem),
            "error_step_index": error_step_index,
            "problem_mismatch": problem_mismatch,
        }


class MockTutorProvider:
    name = "mock"

    def explain(self, *, misconception: str, context: str, language: str,
                problem_text: str = "") -> dict:
        lang = language if language in ("ne", "en") else "en"
        problem = _find_problem(problem_text)
        base = explanation_for(misconception, lang, problem)
        en1, ne1, _, _ = _move(problem)
        if lang == "ne":
            explanation = f"{base} आउनुहोस् सँगै सोचौं: पहिले के गर्नुपर्छ? ({ne1})"
            followup = "यो चरणपछि समीकरण कस्तो देखिन्छ?"
        else:
            explanation = f"{base} Let's think together: what is the first move? ({en1})"
            followup = "After that step, what does the equation look like?"
        return {"explanation": explanation, "followup_question": followup}
