from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Helper"
    app_env: str = "development"

    database_url: str = "sqlite:///./storage/research_helper.sqlite3"
    storage_dir: Path = Path("./storage")
    lancedb_path: Path = Path("./storage/lancedb")

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    chat_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 60
    rag_citation_selection_mode: str = Field(default="precision", pattern="^(current|strict|answer_linked|precision)$")
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 8

    mineru_mode: str = Field(default="auto", pattern="^(auto|api|local)$")
    mineru_api_token: str = ""
    mineru_api_base_url: str = "https://mineru.net/api/v4"
    mineru_use_local: bool = False
    mineru_local_url: str = "http://127.0.0.1:30000"
    mineru_timeout_seconds: int = 600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def input_dir(self) -> Path:
        return self.storage_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.storage_dir / "output"

    @property
    def libraries_output_dir(self) -> Path:
        return self.output_dir / "libraries"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.input_dir.mkdir(parents=True, exist_ok=True)
    settings.libraries_output_dir.mkdir(parents=True, exist_ok=True)
    settings.lancedb_path.mkdir(parents=True, exist_ok=True)
    return settings
