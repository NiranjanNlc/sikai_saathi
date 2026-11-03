"""List models available to your Fireworks key (reads FIREWORKS_API_KEY from .env)."""
import sys
import httpx

sys.path.insert(0, ".")
from backend.app.config import get_settings  # noqa: E402

key = get_settings().fireworks_api_key
if not key:
    raise SystemExit("FIREWORKS_API_KEY not set in .env")
r = httpx.get("https://api.fireworks.ai/inference/v1/models",
              headers={"Authorization": f"Bearer {key}"}, timeout=30)
print("HTTP", r.status_code)
if r.status_code != 200:
    raise SystemExit(r.text[:300])
for m in r.json().get("data", []):
    print(m["id"])
