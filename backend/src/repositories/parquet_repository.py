import hashlib
from datetime import datetime, timezone
from pathlib import Path
import polars as pl
from backend.src.config.settings import settings
from backend.src.config.cache import set_current_etag

class ParquetRepository:
    def __init__(self) -> None:
        self._df: pl.DataFrame | None = None
        self._etag: str = ""
        self._loaded_at: datetime | None = None
        self._gold_path: Path = settings.resolve_path(settings.gold_path)
        self._silver_path: Path = settings.resolve_path(settings.silver_path)

    @property
    def is_loaded(self) -> bool:
        return self._df is not None

    @property
    def etag(self) -> str:
        return self._etag

    @property
    def loaded_at(self) -> datetime | None:
        return self._loaded_at

    @property
    def record_count(self) -> int:
        if self._df is None:
            return 0
        return len(self._df)

    def load(self) -> None:
        if not self._gold_path.exists():
            self._df = None
            self._etag = ""
            return

        self._df = pl.read_parquet(str(self._gold_path))
        self._etag = self._compute_file_hash(self._gold_path)
        self._loaded_at = datetime.now(timezone.utc)

        # sincroniza el etag con el modulo de cache
        set_current_etag(self._etag)

    def reload(self) -> bool:
        if not self._gold_path.exists():
            return False

        new_hash = self._compute_file_hash(self._gold_path)
        if new_hash == self._etag:
            return False

        self.load()
        return True

    def get_all(self, limit: int, offset: int) -> pl.DataFrame:
        if self._df is None:
            return pl.DataFrame()

        total = len(self._df)
        # polars slice no falla si el offset excede el total
        return self._df.slice(offset, min(limit, total - offset))

    def get_by_id(self, global_id: str) -> pl.DataFrame:
        if self._df is None:
            return pl.DataFrame()

        return self._df.filter(pl.col("global_id") == global_id)

    def get_total(self) -> int:
        if self._df is None:
            return 0
        return len(self._df)

    def check_silver_exists(self) -> bool:
        return self._silver_path.exists()

    def check_gold_exists(self) -> bool:
        return self._gold_path.exists()

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)
        return sha.hexdigest()