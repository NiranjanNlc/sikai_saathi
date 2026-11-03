"""Seeded Grade 8 linear-equation problems for the demo."""

from .math_engine import LinearProblem

SEED_PROBLEMS: list[LinearProblem] = [
    LinearProblem(problem_id="demo-3x5-20", a=3, b=5, c=20, text="3x + 5 = 20"),
    LinearProblem(problem_id="seed-2x7-15", a=2, b=7, c=15, text="2x + 7 = 15"),
    LinearProblem(problem_id="seed-4x3-17", a=4, b=-3, c=17, text="4x - 3 = 17"),
    LinearProblem(problem_id="seed-5x4-24", a=5, b=-4, c=24, text="5x - 4 = 24"),
]


def get_problem(problem_id: str) -> LinearProblem | None:
    for p in SEED_PROBLEMS:
        if p.problem_id == problem_id:
            return p
    # Practice variants are derived deterministically; accept any base + suffix.
    if "-p" in problem_id:
        base_id = problem_id.split("-p")[0]
        base = get_problem(base_id)
        if base is None:
            return None
        try:
            index = int(problem_id.split("-p")[1] or "1")
        except ValueError:
            return None
        from .math_engine import generate_similar

        return generate_similar(base, index)
    return None
