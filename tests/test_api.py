"""API integration tests against mock providers (no network, no keys)."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    monkeypatch.setenv("DATABASE_PATH", tmp.name)
    monkeypatch.setenv("DIAGNOSE_PROVIDER", "mock")
    monkeypatch.setenv("TUTOR_PROVIDER", "mock")
    from backend.app.main import app

    with TestClient(app) as c:
        yield c
    os.unlink(tmp.name)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_problems_seeded(client):
    r = client.get("/api/problems")
    assert r.status_code == 200
    texts = [p["text"] for p in r.json()]
    assert "3x + 5 = 20" in texts


def test_diagnose_mock_flags_forgot_to_divide(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s1",
        "problem_id": "demo-3x5-20",
        "language": "en",
        "steps_text": "3x + 5 = 20\n3x = 15\nx = 15",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["suspected_misconception"] == "forgot_to_divide"
    assert body["provider"] == "mock"
    assert body["detected_steps"]


def test_diagnose_requires_input(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s1", "problem_id": "demo-3x5-20",
    })
    assert r.status_code == 422


def test_tutor_mock_nepali(client):
    r = client.post("/api/tutor", json={
        "student_id": "s1",
        "misconception": "forgot_to_divide",
        "language": "ne",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "ne"
    assert body["explanation"]


def test_assessment_correct_and_mastery_flow(client):
    # Demo problem correct: no streak, no mastery yet.
    r = client.post("/api/assessment", json={
        "student_id": "s2", "problem_id": "demo-3x5-20", "answer": 5.0,
    })
    assert r.json()["correct"] is True
    assert r.json()["mastery"] is False
    assert r.json()["streak"] == 0
    # Mastery needs 3 correct practice answers in a row.
    from backend.app.math_engine import LinearProblem, solve
    for i, want_mastery in [(1, False), (2, False), (3, True)]:
        pr = client.get("/api/practice/demo-3x5-20", params={"index": i}).json()
        expected = solve(LinearProblem(pr["problem_id"], pr["a"], pr["b"], pr["c"], pr["text"]))
        r2 = client.post("/api/assessment", json={
            "student_id": "s2", "problem_id": pr["problem_id"], "answer": expected,
        })
        assert r2.json()["correct"] is True
        assert r2.json()["streak"] == i
        assert r2.json()["mastery"] is want_mastery
    # A later wrong answer breaks the streak (and mastery with it).
    pr4 = client.get("/api/practice/demo-3x5-20", params={"index": 4}).json()
    r3 = client.post("/api/assessment", json={
        "student_id": "s2", "problem_id": pr4["problem_id"], "answer": -999.0,
    })
    assert r3.json()["correct"] is False
    assert r3.json()["streak"] == 0
    assert r3.json()["mastery"] is False


def test_assessment_wrong_error_type(client):
    r = client.post("/api/assessment", json={
        "student_id": "s3", "problem_id": "demo-3x5-20", "answer": 15.0,
    })
    body = r.json()
    assert body["correct"] is False
    assert body["error_type"] == "forgot_to_divide"


def test_progress_records_evidence(client):
    client.post("/api/diagnose", json={
        "student_id": "s4", "problem_id": "demo-3x5-20",
        "language": "en", "steps_text": "3x + 5 = 20\nx = 15",
    })
    client.post("/api/assessment", json={
        "student_id": "s4", "problem_id": "demo-3x5-20", "answer": 5.0,
    })
    r = client.get("/api/progress/s4")
    body = r.json()
    assert body["diagnoses"] == 1
    assert body["assessments"] == 1
    assert body["correct"] == 1
    assert body["recent"]


def test_visual_frames_follow_the_problem(client):
    d = client.get("/api/visual/seed-4x3-17", params={"misconception": "forgot_to_divide"}).json()
    assert [(f["left"], f["right"]) for f in d["frames"]] == [
        ("4x - 3", "17"), ("4x", "20"), ("x", "5")]
    assert d["frames"][0]["op_kind"] == "add" and d["frames"][1]["op_kind"] == "divide"
    assert d["error_frame"] == 1


def test_visual_unknown_problem(client):
    assert client.get("/api/visual/nope").status_code == 404


def test_mock_diagnosis_not_hardcoded_to_demo_problem(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s9", "problem_id": "seed-2x7-15", "language": "en",
        "steps_text": "2x + 7 = 15\n2x = 8\nx = 8"}).json()
    assert r["suspected_misconception"] == "forgot_to_divide"
    assert "wasn't divided by 2" in r["evidence"]
    assert r["error_step_index"] == 2
    assert r["problem_mismatch"] is False
    ok = client.post("/api/diagnose", json={
        "student_id": "s9", "problem_id": "seed-2x7-15", "language": "en",
        "steps_text": "2x + 7 = 15\n2x = 8\nx = 4"}).json()
    assert ok["suspected_misconception"] == "correct"


def test_diagnose_sign_error(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s5", "problem_id": "seed-4x3-17", "language": "en",
        "steps_text": "4x - 3 = 17\n4x = 14"}).json()
    assert r["suspected_misconception"] == "sign_error"
    assert r["error_step_index"] == 1


def test_diagnose_one_sided_operation(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s6", "problem_id": "demo-3x5-20", "language": "en",
        "steps_text": "3x + 5 = 20\n3x = 20"}).json()
    assert r["suspected_misconception"] == "one_sided_operation"
    assert r["error_step_index"] == 1


def test_diagnose_image_only_mock_stays_unclear_with_honest_evidence(client):
    # The mock has no vision: image-only input must stay unclear and say
    # so plainly (the frontend branches its guidance on this contract).
    r = client.post("/api/diagnose", json={
        "student_id": "s12", "problem_id": "demo-3x5-20",
        "language": "en", "image_base64": "ZmFrZXBpYw==",
    }).json()
    assert r["suspected_misconception"] == "unclear"
    assert r["provider"] == "mock"
    assert r["error_step_index"] is None
    assert "type your steps" in r["evidence"]


def test_diagnose_unreadable_input_stays_unclear(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s7", "problem_id": "demo-3x5-20", "language": "en",
        "steps_text": "hello"}).json()
    assert r["suspected_misconception"] == "unclear"
    assert r["error_step_index"] is None
    assert "couldn't read" in r["evidence"]


def test_diagnose_problem_mismatch_flagged(client):
    r = client.post("/api/diagnose", json={
        "student_id": "s8", "problem_id": "seed-2x7-15", "language": "en",
        "steps_text": "3x + 5 = 20\n3x = 15\nx = 15"}).json()
    assert r["problem_mismatch"] is True
    assert r["suspected_misconception"] == "unclear"
    assert "don't match" in r["evidence"]


def test_assessment_nepali_message_and_hint_without_reveal(client):
    r = client.post("/api/assessment", json={
        "student_id": "s10", "problem_id": "demo-3x5-20",
        "answer": 15.0, "language": "ne",
    }).json()
    assert r["correct"] is False
    assert r["error_type"] == "forgot_to_divide"
    assert "झन्डै" in r["message"]
    assert r["hint"] and "सङ्केत" in r["hint"]
    # The answer must not leak into the retry message or the hint.
    assert "5" not in r["message"]
    assert "x = 5" not in r["hint"]


def test_license_served(client):
    r = client.get("/license")
    assert r.status_code == 200
    assert "MIT License" in r.text


def test_index_serves_welcome(client):
    r = client.get("/")
    assert r.status_code == 200
    assert 'id="s0"' in r.text
    assert 'id="wStart"' in r.text
    assert 'id="s1"' in r.text


def test_progress_reports_streak(client):
    pr = client.get("/api/practice/demo-3x5-20", params={"index": 1}).json()
    from backend.app.math_engine import LinearProblem, solve
    expected = solve(LinearProblem(pr["problem_id"], pr["a"], pr["b"], pr["c"], pr["text"]))
    client.post("/api/assessment", json={
        "student_id": "s11", "problem_id": pr["problem_id"], "answer": expected,
    })
    body = client.get("/api/progress/s11").json()
    assert body["streak"] == 1
    assert body["mastery_needed"] == 3
    assert body["mastery"] is False
