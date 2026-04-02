from fastapi import APIRouter
from backend.src.schemas.candidates import HealthDetail, HealthResponse

router = APIRouter(tags=["salud"])

def _get_repository():
    from backend.src.main import parquet_repo
    return parquet_repo

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado de salud del sistema",
    description="Verifica la existencia de los archivos Parquet y el estado de carga del dataset Gold.",
)

def health_check():
    repo = _get_repository()
    checks: list[HealthDetail] = []
    all_ok = True

    # verificamos existencia del parquet silver
    silver_exists = repo.check_silver_exists()
    checks.append(HealthDetail(
        name="silver_parquet",
        status="ok" if silver_exists else "missing",
        detail="Archivo Silver disponible" if silver_exists else "Archivo Silver no encontrado en disco",
    ))
    if not silver_exists:
        all_ok = False

    # verificamos existencia del parquet gold
    gold_exists = repo.check_gold_exists()
    checks.append(HealthDetail(
        name="gold_parquet",
        status="ok" if gold_exists else "missing",
        detail="Archivo Gold disponible" if gold_exists else "Archivo Gold no encontrado en disco",
    ))
    if not gold_exists:
        all_ok = False

    # verificamos que el dataframe este cargado en memoria
    data_loaded = repo.is_loaded
    checks.append(HealthDetail(
        name="data_loaded",
        status="ok" if data_loaded else "not_loaded",
        detail=f"{repo.record_count} registros en memoria" if data_loaded else "Dataset no cargado en memoria",
    ))
    if not data_loaded:
        all_ok = False

    overall_status = "healthy" if all_ok else "degraded"

    return HealthResponse(
        status=overall_status,
        loaded_at=repo.loaded_at.isoformat() if repo.loaded_at else None,
        record_count=repo.record_count,
        etag=repo.etag or None,
        checks=checks,
    )