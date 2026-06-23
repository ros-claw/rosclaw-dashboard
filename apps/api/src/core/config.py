from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ROSClaw API"
    debug: bool = False
    database_url: str = "sqlite:///./rosclaw.db"
    duckdb_path: str = "./rosclaw_analytics.duckdb"
    secret_key: str = "rosclaw-dev-secret-key-change-in-production"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    robots_data_path: str = "../../robots"
    practice_dir: Path = Path.home() / ".rosclaw" / "practice" / "runs"
    export_dir: Path = Path.home() / ".rosclaw" / "dashboard" / "exports"
    events_dir: Path = Path.home() / ".rosclaw" / "events"
    report_dir: Path = Path.home() / ".rosclaw" / "dashboard" / "reports"

    class Config:
        env_prefix = "ROSCLAW_"


settings = Settings()
