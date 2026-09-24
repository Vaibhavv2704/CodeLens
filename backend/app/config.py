from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./reviews.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    github_token: str = ""
    api_token: str = ""
    enable_sandbox: bool = False
    sandbox_image: str = "review-sandbox:local"
    simulate_failure: bool = False
    simulated_failure_tool: str = "test_runner"
    max_archive_bytes: int = Field(default=20_000_000, ge=1000)
    max_repository_bytes: int = Field(default=50_000_000, ge=1000)
    max_file_bytes: int = 300_000
    max_files: int = 3000
    max_workers: int = Field(default=2, ge=1, le=8)
    max_queued: int = Field(default=10, ge=1, le=100)

