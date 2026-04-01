from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # rutas a los archivos parquet de las capas del data lake
    silver_path: str = "data/normalized/candidatos_silver.parquet"
    gold_path: str = "data/curated/candidates_gold.parquet"
    audit_log_path: str = "data/curated/audit_log.parquet"

    # cache en memoria
    cache_max_size: int = 256
    cache_ttl_seconds: int = 300

    # paginacion
    pagination_default_limit: int = 20
    pagination_max_limit: int = 100

    # metadatos del app
    app_title: str = "Political Data Peru - API"
    app_version: str = "0.3.0"

    model_config = {"env_prefix": "API_"}

    def resolve_path(self, relative_path: str) -> Path:
        return Path(relative_path)

settings = Settings()