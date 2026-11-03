"""Environment-based configuration. All secrets stay on the backend."""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from the project-root .env (real env vars win)."""
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    diagnose_provider: str  # mock | spark
    tutor_provider: str  # mock | fireworks
    model_api_key: str
    model_base_url: str
    spark_model_id: str
    fireworks_api_key: str
    fireworks_model_id: str
    database_path: str


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        diagnose_provider=os.getenv("DIAGNOSE_PROVIDER", "mock").lower(),
        tutor_provider=os.getenv("TUTOR_PROVIDER", "mock").lower(),
        model_api_key=os.getenv("MODEL_API_KEY", ""),
        model_base_url=os.getenv("MODEL_BASE_URL", "https://api.meta.ai/v1"),
        spark_model_id=os.getenv("SPARK_MODEL_ID", "muse-spark-1.3"),
        fireworks_api_key=os.getenv("FIREWORKS_API_KEY", ""),
        fireworks_model_id=os.getenv("FIREWORKS_MODEL_ID", ""),
        database_path=os.getenv("DATABASE_PATH", "sikai.db"),
    )
