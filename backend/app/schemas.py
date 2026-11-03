"""Typed request/response schemas for the Sikāi orchestrator API."""

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["ne", "en"]


class DiagnoseRequest(BaseModel):
    student_id: str = Field(min_length=1)
    problem_id: str = Field(min_length=1)
    language: Language = "ne"
    image_base64: str | None = None
    steps_text: str | None = None


class DiagnoseResponse(BaseModel):
    detected_steps: list[str]
    suspected_misconception: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    provider: str
    language: str
    error_step_index: int | None = None
    problem_mismatch: bool = False


class TutorRequest(BaseModel):
    student_id: str = Field(min_length=1)
    misconception: str = Field(min_length=1)
    language: Language = "ne"
    context: str = ""
    problem_id: str | None = None


class TutorResponse(BaseModel):
    explanation: str
    followup_question: str
    provider: str
    language: str


class AssessmentRequest(BaseModel):
    student_id: str = Field(min_length=1)
    problem_id: str = Field(min_length=1)
    answer: float
    language: Language = "en"


class AssessmentResponse(BaseModel):
    correct: bool
    expected: float
    error_type: str
    mastery: bool
    attempts: int
    message: str
    hint: str = ""
    streak: int = 0
    mastery_needed: int = 3


class ProgressItem(BaseModel):
    kind: str
    problem_id: str
    detail: str
    created_at: str


class ProgressResponse(BaseModel):
    student_id: str
    diagnoses: int
    assessments: int
    correct: int
    mastery: bool
    recent: list[ProgressItem]
    streak: int = 0
    mastery_needed: int = 3


class ProblemSchema(BaseModel):
    problem_id: str
    a: float
    b: float
    c: float
    text: str


class VisualFrame(BaseModel):
    left: str
    right: str
    op_kind: str | None
    op_value: str | None


class VisualResponse(BaseModel):
    problem_id: str
    text: str
    frames: list[VisualFrame]
    error_frame: int | None
