"""Provider interfaces."""

from typing import Protocol


class DiagnoseProvider(Protocol):
    name: str

    def diagnose(self, *, problem_text: str, image_base64: str | None,
                 steps_text: str | None, language: str) -> dict:
        ...


class TutorProvider(Protocol):
    name: str

    def explain(self, *, misconception: str, context: str, language: str,
                problem_text: str = "") -> dict:
        ...
