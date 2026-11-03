"""Language evaluation: 5 Nepali + 5 English tutoring prompts.

Runs against the configured TUTOR_PROVIDER (mock by default). Real-provider
output is printed for human grading — Nepali quality is NOT assumed.
Usage: uv run python scripts/eval_language.py [--provider mock|fireworks]
"""

import argparse
import os
import sys

sys.path.insert(0, ".")

PROMPTS_NE = [
    "3x + 5 = 20 मा मैले x = 15 लेखें। मेरो गल्ती के हो?",
    "समीकरण भनेको के हो? सरल भाषामा बुझाउनुहोस्।",
    "दुवै पक्षमा एउटै क्रिया किन गर्नुपर्छ?",
    "2x + 7 = 15 हल गर्ने चरणहरू के के हुन्?",
    "मैले चिन्ह बिगारें भने कसरी थाहा पाउने?",
]

PROMPTS_EN = [
    "I wrote x = 15 for 3x + 5 = 20. What is my mistake?",
    "What is an equation? Explain in simple words.",
    "Why must I do the same thing to both sides?",
    "What are the steps to solve 2x + 7 = 15?",
    "How do I know if I made a sign error?",
]


def get_provider(name: str):
    if name == "fireworks":
        from backend.app.config import get_settings
        from backend.app.providers.fireworks import FireworksTutorProvider

        s = get_settings()
        return FireworksTutorProvider(api_key=s.fireworks_api_key, model_id=s.fireworks_model_id)
    from backend.app.providers.mock import MockTutorProvider

    return MockTutorProvider()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=os.getenv("TUTOR_PROVIDER", "mock"))
    args = parser.parse_args()
    try:
        provider = get_provider(args.provider)
    except ValueError as exc:
        print(f"Provider '{args.provider}' unavailable: {exc}")
        print("Falling back to mock for structure check.")
        provider = get_provider("mock")
    print(f"# Language eval — provider: {provider.name}\n")
    for i, prompt in enumerate(PROMPTS_NE, 1):
        out = provider.explain(misconception="one_sided_operation", context=prompt, language="ne")
        print(f"## NE-{i}: {prompt}\n{out['explanation']}\n")
    for i, prompt in enumerate(PROMPTS_EN, 1):
        out = provider.explain(misconception="one_sided_operation", context=prompt, language="en")
        print(f"## EN-{i}: {prompt}\n{out['explanation']}\n")
    print("Grade each reply 0-2 (wrong/partial/good). Nepali must be human-checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
