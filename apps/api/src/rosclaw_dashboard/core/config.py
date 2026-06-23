from pathlib import Path

from pydantic_settings import BaseSettings

from rosclaw_dashboard.core.workspace import resolve_rosclaw_home


class Settings(BaseSettings):
    app_name: str = "ROSClaw API"
    debug: bool = False
    database_url: str = "sqlite:///./rosclaw.db"
    duckdb_path: str = "./rosclaw_analytics.duckdb"
    secret_key: str = "rosclaw-dev-secret-key-change-in-production"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    robots_data_path: str = "../../robots"
    practice_dir: Path = resolve_rosclaw_home() / "data" / "practice" / "runs"
    episodes_dir: Path = resolve_rosclaw_home() / "artifacts" / "episodes"
    export_dir: Path = resolve_rosclaw_home() / "dashboard" / "exports"
    events_dir: Path = resolve_rosclaw_home() / "events"
    report_dir: Path = resolve_rosclaw_home() / "dashboard" / "reports"

    class Config:
        env_prefix = "ROSCLAW_"


settings = Settings()
