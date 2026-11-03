"""Sikāi Orchestrator: FastAPI routes, provider selection, deterministic checks."""

from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .config import get_settings
from .math_engine import (
    analyze_numeric_answer, check_answer, diagnose_steps,
    diagnosis_evidence, error_frame_index, generate_similar,
    practice_hint, solution_steps, solve,
)
from .providers.fireworks import FireworksTutorProvider, ProviderError as FWError
from .providers.mock import (
    MockDiagnoseProvider, MockTutorProvider, explanation_for,
)
from .providers.spark import ProviderError as SparkError, SparkDiagnoseProvider
from .schemas import (
    AssessmentRequest,
    AssessmentResponse,
    DiagnoseRequest,
    DiagnoseResponse,
    ProblemSchema,
    ProgressItem,
    ProgressResponse,
    TutorRequest,
    TutorResponse,
    VisualResponse,
)
from .seed import SEED_PROBLEMS, get_problem

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

@asynccontextmanager
async def _lifespan(_: FastAPI):
    db.init_db(get_settings().database_path)
    yield


app = FastAPI(title="Sikāi Sathi API", version="0.1.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _diagnose_provider():
    settings = get_settings()
    if settings.diagnose_provider == "spark":
        try:
            return SparkDiagnoseProvider(
                api_key=settings.model_api_key, base_url=settings.model_base_url,
                model_id=settings.spark_model_id,
            ), False
        except ValueError:
            return MockDiagnoseProvider(), True
    return MockDiagnoseProvider(), False


def _tutor_provider():
    settings = get_settings()
    if settings.tutor_provider == "fireworks":
        try:
            return FireworksTutorProvider(
                api_key=settings.fireworks_api_key,
                model_id=settings.fireworks_model_id,
            ), False
        except ValueError:
            return MockTutorProvider(), True
    return MockTutorProvider(), False


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "diagnose_provider": settings.diagnose_provider,
        "tutor_provider": settings.tutor_provider,
    }


@app.get("/api/problems", response_model=list[ProblemSchema])
def list_problems() -> list[dict]:
    return [p.__dict__ for p in SEED_PROBLEMS]


@app.post("/api/diagnose", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest) -> dict:
    problem = get_problem(req.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Unknown problem_id")
    if not req.image_base64 and not req.steps_text:
        raise HTTPException(
            status_code=422, detail="Provide image_base64 or steps_text"
        )
    provider, fell_back = _diagnose_provider()
    try:
        out = provider.diagnose(
            problem_text=problem.text,
            image_base64=req.image_base64,
            steps_text=req.steps_text,
            language=req.language,
        )
        used = provider.name
    except SparkError as exc:
        # Provider fallback state: real error surfaced, mock fills the demo.
        out = MockDiagnoseProvider().diagnose(
            problem_text=problem.text,
            image_base64=req.image_base64,
            steps_text=req.steps_text,
            language=req.language,
        )
        out["evidence"] = f"{out['evidence']} (Spark unavailable: {exc})"
        used = "mock-fallback"
    fallback_note = ""
    if fell_back:
        fallback_note = " (Spark not configured; mock used.)"
        used = "mock-fallback"

    # Deterministic truth: typed steps are always diagnosed by the math
    # engine, never by the LLM. The provider only explains or reads photos.
    error_step_index = out.get("error_step_index")
    problem_mismatch = bool(out.get("problem_mismatch", False))
    if req.steps_text:
        det = diagnose_steps(
            problem,
            [s.strip() for s in req.steps_text.splitlines() if s.strip()],
        )
        out["detected_steps"] = [
            s.strip() for s in req.steps_text.splitlines() if s.strip()
        ]
        out["suspected_misconception"] = det["misconception"]
        out["evidence"] = diagnosis_evidence(problem, det, req.language)
        out["explanation"] = explanation_for(
            det["misconception"], req.language, problem
        )
        out["confidence"] = {
            "correct": 0.95, "forgot_to_divide": 0.9, "sign_error": 0.9,
            "one_sided_operation": 0.9, "arithmetic_error": 0.7,
        }.get(det["misconception"], 0.3)
        error_step_index = det["error_step_index"]
        problem_mismatch = det["problem_mismatch"]
    if fallback_note:
        out["evidence"] = out["evidence"] + fallback_note

    settings = get_settings()
    db.init_db(settings.database_path)
    db.record_diagnosis(
        settings.database_path, req.student_id, req.problem_id,
        out["suspected_misconception"], float(out["confidence"]),
    )
    return DiagnoseResponse(
        detected_steps=out["detected_steps"],
        suspected_misconception=out["suspected_misconception"],
        evidence=out["evidence"],
        confidence=float(out["confidence"]),
        explanation=out["explanation"],
        provider=used,
        language=req.language,
        error_step_index=error_step_index,
        problem_mismatch=problem_mismatch,
    ).model_dump()


@app.post("/api/tutor", response_model=TutorResponse)
def tutor(req: TutorRequest) -> dict:
    provider, fell_back = _tutor_provider()
    prob = get_problem(req.problem_id) if req.problem_id else None
    problem_text = prob.text if prob else ""
    try:
        out = provider.explain(
            misconception=req.misconception, context=req.context,
            language=req.language, problem_text=problem_text,
        )
        used = provider.name
    except FWError as exc:
        out = MockTutorProvider().explain(
            misconception=req.misconception, context=req.context,
            language=req.language, problem_text=problem_text,
        )
        out["explanation"] = f"{out['explanation']} (Fireworks unavailable: {exc})"
        used = "mock-fallback"
    if fell_back:
        used = "mock-fallback"
    return TutorResponse(
        explanation=out["explanation"],
        followup_question=out.get("followup_question", ""),
        provider=used,
        language=req.language,
    ).model_dump()


@app.get("/api/visual/{problem_id}", response_model=VisualResponse)
def visual(problem_id: str, misconception: str = "") -> dict:
    problem = get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Unknown problem_id")
    return {
        "problem_id": problem_id,
        "text": problem.text,
        "frames": solution_steps(problem),
        "error_frame": error_frame_index(problem, misconception),
    }


@app.post("/api/assessment", response_model=AssessmentResponse)
def assess(req: AssessmentRequest) -> dict:
    problem = get_problem(req.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Unknown problem_id")
    # Deterministic: only the math engine decides correctness/mastery.
    correct = check_answer(problem, req.answer)
    error_type = analyze_numeric_answer(problem, req.answer)
    settings = get_settings()
    db.init_db(settings.database_path)
    attempts = db.record_assessment(
        settings.database_path, req.student_id, req.problem_id,
        req.answer, correct, error_type,
    )
    mastery = db.student_has_mastery(settings.database_path, req.student_id)
    streak = db.practice_streak(settings.database_path, req.student_id)
    expected = solve(problem)
    # This message is about THIS attempt only; overall progress travels
    # separately in streak/mastery so the two can never contradict.
    ne = req.language == "ne"
    if correct:
        if mastery:
            message = ("सही! लगातार 3 वटा सही — यो सीप पक्का भयो!" if ne else
                       "Correct! 3 in a row — you've mastered this skill!")
        else:
            left = db.MASTERY_NEEDED - streak
            message = (f"सही! यो सीप पक्का गर्न अझै {left}।" if ne else
                       f"Correct! {left} more to master this skill.")
    elif error_type == "forgot_to_divide":
        message = ("झन्डै! दुवै पक्षलाई भाग गरेर फेरि हेर।" if ne else
                   "Almost! Divide both sides once more and try again.")
    elif error_type == "sign_error":
        message = ("'=' पार गर्दा चिन्ह जाँच।" if ne else
                   "Check the sign when moving a term across '='.")
    else:
        message = ("मिलेन। दुवै पक्षमा उल्टो क्रिया गरेर हेर।" if ne else
                   "Not quite. Try the inverse operation on both sides.")
    hint = "" if correct else practice_hint(problem, error_type, req.language)
    return AssessmentResponse(
        correct=correct, expected=expected, error_type=error_type,
        mastery=mastery, attempts=attempts, message=message,
        hint=hint, streak=streak, mastery_needed=db.MASTERY_NEEDED,
    ).model_dump()


@app.get("/api/practice/{problem_id}", response_model=ProblemSchema)
def practice(problem_id: str, index: int = 1) -> dict:
    base = get_problem(problem_id)
    if base is None:
        raise HTTPException(status_code=404, detail="Unknown problem_id")
    return generate_similar(base, index).__dict__


@app.get("/api/progress/{student_id}", response_model=ProgressResponse)
def progress(student_id: str) -> dict:
    settings = get_settings()
    db.init_db(settings.database_path)
    data = db.get_progress(settings.database_path, student_id)
    mastery = db.student_has_mastery(settings.database_path, student_id)
    streak = db.practice_streak(settings.database_path, student_id)
    return ProgressResponse(
        student_id=student_id,
        diagnoses=data["diagnoses"],
        assessments=data["assessments"],
        correct=data["correct"],
        mastery=mastery,
        recent=[ProgressItem(**r) for r in data["recent"]],
        streak=streak,
        mastery_needed=db.MASTERY_NEEDED,
    ).model_dump()


# Serve the demo frontend (Submit → Diagnosis → Learn → Practice) from /.
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "index.html"))
