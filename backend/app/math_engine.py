"""Deterministic learning engine for Grade 8 linear equations.

Form: a*x + b = c. The LLM never decides correctness, misconceptions
or mastery; only this module does.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LinearProblem:
    problem_id: str
    a: float
    b: float
    c: float
    text: str


TOLERANCE = 1e-6


def solve(problem: LinearProblem) -> float:
    """Exact solution x = (c - b) / a."""
    if problem.a == 0:
        raise ValueError("Coefficient 'a' must be non-zero")
    return (problem.c - problem.b) / problem.a


def is_close(x: float, y: float, tol: float = TOLERANCE) -> bool:
    return abs(x - y) <= tol


def check_answer(problem: LinearProblem, answer: float) -> bool:
    """Deterministic correctness check."""
    return is_close(answer, solve(problem))


def analyze_numeric_answer(problem: LinearProblem, answer: float) -> str:
    """Classify a wrong numeric answer into a deterministic error type.

    Returns one of: correct, forgot_to_divide, divided_only_c,
    sign_error, arithmetic_error.
    """
    if check_answer(problem, answer):
        return "correct"
    a, b, c = problem.a, problem.b, problem.c
    expected = solve(problem)
    candidates = {
        "forgot_to_divide": c - b,  # e.g. 3x+5=20 -> x=15
        "divided_only_c": c / a if a != 0 else None,  # e.g. x=20/3
        "sign_error": (b - c) / a if a != 0 else None,  # flipped sign
        "added_instead": (c + b) / a if a != 0 else None,
    }
    for error_type, value in candidates.items():
        if value is not None and is_close(answer, value):
            return error_type
    # Near-miss counts as arithmetic slip, far-miss as generic arithmetic error.
    if abs(answer - expected) <= max(2.0, abs(expected)):
        return "arithmetic_error"
    return "arithmetic_error"


def generate_similar(problem: LinearProblem, index: int = 1) -> LinearProblem:
    """Deterministically derive a practice variant with an integer solution."""
    base = int(abs(problem.a)) + index
    a = float(base if base > 1 else 2)
    x = float(int(solve(problem)) + index)
    b = float(int(problem.b) + index)
    c = a * x + b
    pid = f"{problem.problem_id}-p{index}"
    return LinearProblem(
        problem_id=pid,
        a=a,
        b=b,
        c=c,
        text=f"{_lhs(a, b)} = {fmt(c)}",
    )


def fmt(n: float) -> str:
    """Format a number without a trailing .0."""
    return str(int(n)) if float(n).is_integer() else f"{n:g}"


def _lhs(a: float, b: float) -> str:
    coef = "" if a == 1 else ("-" if a == -1 else fmt(a))
    left = f"{coef}x"
    if b > 0:
        left += f" + {fmt(b)}"
    elif b < 0:
        left += f" - {fmt(abs(b))}"
    return left


def solution_steps(problem: LinearProblem) -> list[dict]:
    """Deterministic worked solution as balance-scale frames.

    Each frame is {left, right, op_kind, op_value}; op_* describes the move
    that LEADS TO the next frame (None on the last frame).
    """
    a, b, c = problem.a, problem.b, problem.c
    frames: list[dict] = [{"left": _lhs(a, b), "right": fmt(c),
                           "op_kind": None, "op_value": None}]
    cur_right = c
    if b != 0:
        frames[-1]["op_kind"] = "subtract" if b > 0 else "add"
        frames[-1]["op_value"] = fmt(abs(b))
        cur_right = c - b
        frames.append({"left": _lhs(a, 0), "right": fmt(cur_right),
                       "op_kind": None, "op_value": None})
    if a != 1:
        frames[-1]["op_kind"] = "divide"
        frames[-1]["op_value"] = fmt(a)
        frames.append({"left": "x", "right": fmt(cur_right / a),
                       "op_kind": None, "op_value": None})
    return frames


def error_frame_index(problem: LinearProblem, misconception: str) -> int | None:
    """Which frame the student's mistake relates to (None = no specific one)."""
    frames = solution_steps(problem)
    if misconception == "forgot_to_divide":
        return max(len(frames) - 2, 0)
    if misconception in ("one_sided_operation", "sign_error"):
        return 0
    return None


# ---------------------------------------------------------------------------
# Deterministic step-level diagnosis.
# Knows: correct, forgot_to_divide, sign_error, one_sided_operation,
# arithmetic_error, unclear. Never guesses: unparseable input stays "unclear".
# ---------------------------------------------------------------------------

_NUM = r"-?\d+(?:\.\d+)?"


def _safe_number(text: str) -> float | None:
    """Parse a plain number or a simple 'num op num' expression."""
    s = (text or "").strip().replace("−", "-").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    m = re.fullmatch(f"({_NUM})([+*/-])({_NUM})", s)
    if not m:
        return None
    x, op, y = float(m.group(1)), m.group(2), float(m.group(3))
    try:
        if op == "+":
            return x + y
        if op == "-":
            return x - y
        if op == "*":
            return x * y
        return x / y
    except ZeroDivisionError:
        return None


def _parse_linear_side(text: str) -> tuple[float, float] | None:
    """Parse 'ax + b' (x-term first) into (a, b)."""
    s = (text or "").strip().replace(" ", "").replace("*", "").replace("−", "-")
    if s.count("x") != 1:
        return None
    before, _, after = s.partition("x")
    if before in ("", "+"):
        a = 1.0
    elif before == "-":
        a = -1.0
    else:
        try:
            a = float(before)
        except ValueError:
            return None
    if after == "":
        return (a, 0.0)
    m = re.fullmatch(r"([+-])(\d+(?:\.\d+)?)", after)
    if not m:
        return None
    b = float(m.group(2)) if m.group(1) == "+" else -float(m.group(2))
    return (a, b)


def parse_step_line(line: str) -> tuple[str, object] | None:
    """Parse one typed step.

    Returns ("equation", (a, b, c)) for 'ax+b=c' in any orientation,
    ("value", v) for a bare final-number claim, else None.
    """
    s = (line or "").strip().replace("−", "-")
    if not s:
        return None
    if "=" not in s:
        if "x" in s.lower():
            return None
        v = _safe_number(s)
        return ("value", v) if v is not None else None
    left, _, right = s.partition("=")
    if "=" in right:
        return None
    has_left, has_right = "x" in left.lower(), "x" in right.lower()
    if has_left and has_right:
        return None
    if not has_left and not has_right:
        return None
    lin_text, num_text = (left, right) if has_left else (right, left)
    lin = _parse_linear_side(lin_text)
    num = _safe_number(num_text)
    if lin is None or num is None:
        return None
    return ("equation", (lin[0], lin[1], num))


def _fault(misconception: str, index: int | None, detail: str,
           mismatch: bool = False) -> dict:
    return {
        "misconception": misconception,
        "error_step_index": index,
        "problem_mismatch": mismatch,
        "detail": detail,
    }


def diagnose_steps(problem: LinearProblem, steps: list[str]) -> dict:
    """Deterministically diagnose typed steps against a problem.

    Returns {"misconception", "error_step_index" (0-based, None = no
    specific line), "problem_mismatch", "detail"}.
    """
    cleaned = [s.strip() for s in (steps or []) if s and s.strip()]
    if not cleaned:
        return _fault("unclear", None, "empty")
    parsed = [parse_step_line(s) for s in cleaned]
    eq_lines = [(i, p[1]) for i, p in enumerate(parsed)
                if p is not None and p[0] == "equation"]
    if not eq_lines:
        return _fault("unclear", None, "unreadable")

    a0, b0, c0 = problem.a, problem.b, problem.c
    # Line 1 check: a full restatement that differs from the problem means
    # the steps belong to another question — do not diagnose them as if not.
    first_a, first_b, first_c = eq_lines[0][1]
    if not is_close(first_b, 0.0) and not (
        is_close(first_a, a0) and is_close(first_b, b0)
        and is_close(first_c, c0)
    ):
        return _fault("unclear", None, "mismatch", mismatch=True)

    if a0 == 0:
        return _fault("unclear", None, "unreadable")
    reduced_rhs = c0 - b0
    expected = reduced_rhs / a0

    def classify_final(value: float) -> str:
        if is_close(value, expected):
            return "correct"
        if a0 != 1 and is_close(value, reduced_rhs):
            return "forgot_to_divide"
        engine = analyze_numeric_answer(problem, value)
        return {
            "forgot_to_divide": "forgot_to_divide",
            "sign_error": "sign_error",
            "added_instead": "sign_error",
            "divided_only_c": "one_sided_operation",
        }.get(engine, "arithmetic_error")

    for i, (a, b, c) in eq_lines:
        if not is_close(b, 0.0):
            continue  # full restatement of the problem; nothing to judge
        if not is_close(a, 1.0):
            if not is_close(a, a0):
                return _fault("arithmetic_error", i, "wrong_coefficient")
            if is_close(c, c0) and not is_close(b0, 0.0):
                # Dropped the constant, other side untouched: 3x+5=20 → 3x=20.
                return _fault("one_sided_operation", i, "dropped_constant")
            if is_close(c, c0 + b0) and not is_close(c, reduced_rhs):
                # Flipped the move: 4x-3=17 → 4x=14 (should be 20).
                return _fault("sign_error", i, "flipped_move")
            if is_close(c, reduced_rhs):
                continue
            return _fault("arithmetic_error", i, "bad_reduce")
        verdict = classify_final(c)
        if verdict != "correct":
            return _fault(verdict, i, "bad_final")

    # A bare trailing number ("15") is a final-answer claim too.
    for i, p in enumerate(parsed):
        if p is not None and p[0] == "value":
            verdict = classify_final(float(p[1]))
            if verdict != "correct":
                return _fault(verdict, i, "bad_final")

    _, (la, lb, _) = eq_lines[-1]
    if is_close(lb, 0.0) and not is_close(la, 1.0) and a0 != 1:
        # Stopped one step early: 3x+5=20 → 3x=15, no final line.
        return _fault("forgot_to_divide", None, "incomplete")
    return _fault("correct", None, "all_correct")


def diagnosis_evidence(problem: LinearProblem, diagnosis: dict, lang: str) -> str:
    """Student-language evidence line (growth tone, never algebra jargon)."""
    ne = lang == "ne"
    misc, detail = diagnosis["misconception"], diagnosis.get("detail", "")
    idx = diagnosis.get("error_step_index")
    line = f"लाइन {idx + 1} हेर: " if ne and idx is not None \
        else f"Look at line {idx + 1}: " if idx is not None else ""
    a0, b0, c0 = problem.a, problem.b, problem.c
    mid = fmt(c0 - b0)
    if misc == "forgot_to_divide":
        if detail == "incomplete":
            return (f"तिमी एउटा चरण अगाडि रोकियौ — {fmt(a0)}x = {mid} पछि "
                    f"दुवै पक्षलाई {fmt(a0)} ले भाग गर।" if ne else
                    f"You stopped one step early — after {fmt(a0)}x = {mid}, "
                    f"divide both sides by {fmt(a0)}.")
        return (f"{line}{fmt(a0)}x बाट x भयो, तर {mid} लाई {fmt(a0)} ले "
                f"भाग गरिएन।" if ne else
                f"{line}{fmt(a0)}x became x, but {mid} wasn't divided "
                f"by {fmt(a0)}.")
    if misc == "sign_error":
        return (f"{line}'=' पार गर्दा चिन्ह उल्टो हुन्छ — अर्को पक्ष "
                f"{fmt(c0 - b0)} हुनुपर्छ।" if ne else
                f"{line}moving a term across '=' flips its sign — the other "
                f"side should be {fmt(c0 - b0)}.")
    if misc == "one_sided_operation":
        return (f"{line}एउटा पक्ष बदलियो तर अर्को {fmt(c0)} नै रह्यो। एउटा "
                f"पक्षमा जे गर्छौ, अर्कोमा पनि त्यही गर।" if ne else
                f"{line}one side changed but the other stayed {fmt(c0)}. "
                f"Whatever you do to one side, do the same to the other.")
    if misc == "arithmetic_error":
        return (f"{line}तरिका सही छ तर हिसाब बिग्रियो — अङ्क फेरि जाँच।"
                if ne else
                f"{line}the move is right but the arithmetic slipped — "
                f"check the numbers.")
    if misc == "correct":
        return ("हरेक चरणमा दुवै पक्षमा एउटै क्रिया लागू भएको छ। स्याबास!"
                if ne else
                "Each step applies the same operation to both sides. Well done!")
    if detail == "mismatch":
        return ("तिम्रा चरणहरू यो प्रश्नसँग मिलेनन्। सही प्रश्न छान्यौ कि "
                "छैनौ हेर।" if ne else
                "Your steps don't match this problem. "
                "Check you picked the right question.")
    if detail == "empty":
        return ("आफ्नो कामको फोटो राख वा चरणहरू टाइप गर।" if ne else
                "Add a photo of your work or type your steps.")
    return ("ती चरणहरू पढ्न सकिनँ। अझ स्पष्ट फोटो खिच वा हरेक चरण "
            "छुट्टाछुट्टै लाइनमा लेख।" if ne else
            "I couldn't read those steps. Try a clearer photo or type one "
            "step per line.")


def practice_hint(problem: LinearProblem, error_type: str, lang: str) -> str:
    """A hint that teaches the next move without revealing the answer."""
    ne = lang == "ne"
    a0, b0, c0 = problem.a, problem.b, problem.c
    mid = fmt(c0 - b0)
    if error_type == "forgot_to_divide":
        return (f"सङ्केत: {fmt(a0)}x = {mid} पछि '× {fmt(a0)}' लाई के ले हटाउँछ?"
                if ne else
                f"Hint: after {fmt(a0)}x = {mid}, what undoes '× {fmt(a0)}'?")
    if error_type == "sign_error":
        return ("सङ्केत: + पार गर्दा − हुन्छ, − पार गर्दा + हुन्छ। तिमीले कुन सार्यौ?"
                if ne else
                "Hint: moving + makes − and moving − makes +. Which did you move?")
    if error_type in ("one_sided_operation", "divided_only_c"):
        return ("सङ्केत: एउटा पक्षमा जे गर्छौ, अर्कोमा पनि त्यही गर।"
                if ne else
                "Hint: whatever you do to one side, do the same to the other side.")
    if error_type == "arithmetic_error":
        return ("सङ्केत: तरिका सही छ — हिसाब बिस्तारै फेरि गर।" if ne else
                "Hint: the method is right — redo the calculation slowly.")
    return ""
