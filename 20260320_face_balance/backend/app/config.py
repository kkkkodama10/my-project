import yaml
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://facegraph:facegraph@localhost:5432/facegraph"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "facegraph-images"

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_analysis_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yml"
    with open(config_path) as f:
        return yaml.safe_load(f)


settings = Settings()
analysis_config = load_analysis_config()
