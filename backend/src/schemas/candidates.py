from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

class CandidateResponse(BaseModel):
    global_id: str
    dni: str | None = None
    nombres: str | None = None
    apellido_paterno: str | None = None
    apellido_materno: str | None = None
    partido: str | None = None
    cargo: str | None = None
    source_category: str | None = None

    # metricas financieras y patrimoniales
    ingresos_totales: float | None = None
    valor_total_bienes: float | None = None
    conteo_sentencias: int | None = None
    experiencia_publica_anios: int | None = None
    cantidad_renuncias: int | None = None

    # scores del motor de riesgo
    score_financiero: float | None = None
    score_legal: float | None = None
    score_estabilidad: float | None = None
    score_itr: float | None = None

    # flags y contexto
    risk_flags: list[str] = Field(default_factory=list)
    search_context: str | None = None
    model_config = {"from_attributes": True}

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    limit: int
    offset: int
    has_next: bool

class HealthDetail(BaseModel):
    name: str
    status: str
    detail: str | None = None

class HealthResponse(BaseModel):
    status: str
    loaded_at: str | None = None
    record_count: int = 0
    etag: str | None = None
    checks: list[HealthDetail] = Field(default_factory=list)