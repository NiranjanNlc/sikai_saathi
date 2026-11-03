"""Tests for the deterministic math engine (correctness lives here only)."""

import pytest

from backend.app.math_engine import (
    LinearProblem,
    analyze_numeric_answer,
    check_answer,
    diagnose_steps,
    generate_similar,
    parse_step_line,
    solve,
)

DEMO = LinearProblem(problem_id="demo-3x5-20", a=3, b=5, c=20, text="3x + 5 = 20")


def test_solve_demo():
    assert solve(DEMO) == pytest.approx(5.0)


def test_solve_rejects_zero_a():
    with pytest.raises(ValueError):
        solve(LinearProblem(problem_id="bad", a=0, b=1, c=2, text="bad"))


def test_check_answer_correct_and_tolerance():
    assert check_answer(DEMO, 5.0)
    assert check_answer(DEMO, 5.0 + 1e-9)
    assert not check_answer(DEMO, 5.1)


def test_forgot_to_divide():
    # 20 - 5 = 15 without dividing by 3.
    assert analyze_numeric_answer(DEMO, 15.0) == "forgot_to_divide"


def test_sign_error():
    # (5 - 20) / 3 = -5.
    assert analyze_numeric_answer(DEMO, -5.0) == "sign_error"


def test_correct_classification():
    assert analyze_numeric_answer(DEMO, 5.0) == "correct"


def test_generate_similar_has_integer_solution():
    variant = generate_similar(DEMO, 1)
    assert check_answer(variant, solve(variant))
    assert abs(solve(variant) - round(solve(variant))) < 1e-9


def test_practice_text_has_clean_signs():
    from backend.app.math_engine import generate_similar
    from backend.app.seed import get_problem
    p = generate_similar(get_problem("seed-4x3-17"), 1)
    assert "+ -" not in p.text and "- " in p.text


def test_parse_step_line_forms():
    assert parse_step_line("3x + 5 = 20") == ("equation", (3.0, 5.0, 20.0))
    assert parse_step_line("x = 15") == ("equation", (1.0, 0.0, 15.0))
    assert parse_step_line("20 = 3x + 5") == ("equation", (3.0, 5.0, 20.0))
    assert parse_step_line("hello") is None
    assert parse_step_line("3x + = 20") is None


def test_diagnose_steps_forgot_to_divide():
    d = diagnose_steps(DEMO, ["3x + 5 = 20", "3x = 15", "x = 15"])
    assert (d["misconception"], d["error_step_index"]) == ("forgot_to_divide", 2)


def test_diagnose_steps_correct():
    d = diagnose_steps(DEMO, ["3x + 5 = 20", "3x = 15", "x = 5"])
    assert d["misconception"] == "correct"
    assert d["error_step_index"] is None


def test_diagnose_steps_sign_error():
    p = LinearProblem(problem_id="s", a=4, b=-3, c=17, text="4x - 3 = 17")
    d = diagnose_steps(p, ["4x - 3 = 17", "4x = 14"])
    assert (d["misconception"], d["error_step_index"]) == ("sign_error", 1)


def test_diagnose_steps_one_sided():
    d = diagnose_steps(DEMO, ["3x + 5 = 20", "3x = 20"])
    assert (d["misconception"], d["error_step_index"]) == ("one_sided_operation", 1)


def test_diagnose_steps_unreadable_and_mismatch():
    assert diagnose_steps(DEMO, ["hello"])["misconception"] == "unclear"
    assert diagnose_steps(DEMO, [])["detail"] == "empty"
    other = LinearProblem(problem_id="o", a=2, b=7, c=15, text="2x + 7 = 15")
    d = diagnose_steps(other, ["3x + 5 = 20", "3x = 15", "x = 15"])
    assert d["problem_mismatch"] is True
    assert d["misconception"] == "unclear"


def test_diagnose_steps_incomplete_counts_as_one_step_left():
    d = diagnose_steps(DEMO, ["3x + 5 = 20", "3x = 15"])
    assert d["misconception"] == "forgot_to_divide"
    assert d["detail"] == "incomplete"
