import polars as pl
from backend.src.repositories.parquet_repository import ParquetRepository
from backend.src.schemas.candidates import CandidateResponse, PaginatedResponse
from backend.src.config.settings import settings

class CandidateService:
    def __init__(self, repository: ParquetRepository) -> None:
        self._repo = repository

    def list_candidates(
        self, limit: int | None = None, offset: int = 0
    ) -> PaginatedResponse[CandidateResponse]:
        effective_limit = min(
            limit or settings.pagination_default_limit,
            settings.pagination_max_limit,
        )

        df = self._repo.get_all(effective_limit, offset)
        total = self._repo.get_total()
        candidates = self._dataframe_to_responses(df)

        return PaginatedResponse[CandidateResponse](
            data=candidates,
            total=total,
            limit=effective_limit,
            offset=offset,
            has_next=(offset + effective_limit) < total,
        )

    def get_candidate(self, global_id: str) -> CandidateResponse | None:
        df = self._repo.get_by_id(global_id)

        if df.is_empty():
            return None

        candidates = self._dataframe_to_responses(df)
        return candidates[0]

    def _dataframe_to_responses(
        self, df: pl.DataFrame
    ) -> list[CandidateResponse]:
        records = df.to_dicts()
        responses = []

        for row in records:
            # risk_flags puede venir como lista de listas desde polars
            raw_flags = row.get("risk_flags")
            if raw_flags is None:
                row["risk_flags"] = []
            elif isinstance(raw_flags, list):
                # aplanamos en caso de que hayan sublistas
                flat = []
                for item in raw_flags:
                    if isinstance(item, list):
                        flat.extend([f for f in item if f is not None])
                    elif item is not None:
                        flat.append(item)
                row["risk_flags"] = flat

            responses.append(CandidateResponse(**row))

        return responses