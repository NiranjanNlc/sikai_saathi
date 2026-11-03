# Project Brief: Sikāi Sathi

Build a Nepal-first AI learning companion for Grade 8 students, initially focused on mathematics.

## Product vision
Sikāi Sathi helps students understand their mistakes rather than memorize answers.

Tagline: Your learning companion. Your language. Your pace.

## Primary demo
A student uploads a photo of handwritten work solving:

3x + 5 = 20

The application:
1. Analyzes the student's handwritten solution.
2. Identifies the mathematical error or misconception.
3. Explains the mistake in simple Nepali or English.
4. Provides a visual explanation where useful.
5. Asks the student to solve a similar problem.
6. Checks the answer using deterministic Python logic.
7. Records evidence of learning.

## Technology
- Backend: Python + FastAPI, if compatible with existing architecture.
- Frontend: reuse the existing frontend; do not rewrite it unnecessarily.
- Database: reuse existing persistence where possible.
- Meta Model API: Muse Spark for image understanding and diagnosis.
- Fireworks AI: hosted Meta open-weight model for a separately tested tutoring route.
- Muse Image: generate educational illustrations if time permits.

## Important constraints
- Nepali language quality is NOT assumed. Test it before relying on it.
- Support English as a reliable fallback.
- Do not claim official Nepal curriculum alignment without verified curriculum data.
- Never allow an LLM to decide mathematical correctness or mastery by itself.
- Keep API keys on the backend.
- Do not fabricate model responses.
- Include loading, error and provider-fallback states.

## Scope
Build one excellent end-to-end demonstration for Grade 8 linear equations.

Do not build a full learning management system, teacher dashboard, voice assistant, offline sync, or complete SEE curriculum.

## Delivery requirements
- Working application
- Working backend API
- One complete student learning journey
- Seeded example problems
- README with setup instructions
- Demo script
- Basic tests for mathematical verification and API integration

Prioritize a working, testable vertical slice over architectural complexity.
