from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from backend.src.config.cache import (
    apply_cache_headers,
    build_cache_key,
    check_etag_match,
    get_cached,
    set_cached,
)
from backend.src.config.settings import settings
from backend.src.schemas.candidates import CandidateResponse, PaginatedResponse

router = APIRouter(prefix="/v1", tags=["candidatos"])

def _get_service():
    from backend.src.main import candidate_service
    return candidate_service

@router.get(
    "/candidatos",
    response_model=PaginatedResponse[CandidateResponse],
    summary="Lista paginada de candidatos",
    description="Devuelve candidatos de la Capa Gold con paginación offset/limit y soporte ETag.",
)
def list_candidates(
    request: Request,
    response: Response,
    limit: int = Query(
        default=settings.pagination_default_limit,
        ge=1,
        le=settings.pagination_max_limit,
        description="Cantidad de registros por página",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Desplazamiento desde el inicio del dataset",
    ),
):
    # si el cliente tiene la misma version, ahorramos ancho de banda
    if check_etag_match(request):
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    # verificamos si hay una respuesta cacheada para estos parametros
    cache_key = build_cache_key(request)
    cached = get_cached(cache_key)
    if cached is not None:
        apply_cache_headers(response)
        return cached

    service = _get_service()
    result = service.list_candidates(limit=limit, offset=offset)

    # guardamos en cache y inyectamos headers
    set_cached(cache_key, result)
    apply_cache_headers(response)

    return result

@router.get(
    "/candidato/{global_id}",
    response_model=CandidateResponse,
    summary="Detalle de un candidato",
    description="Busca un candidato por su Global ID (UUID v5 determinista).",
)
def get_candidate(
    global_id: str,
    request: Request,
    response: Response,
):
    if check_etag_match(request):
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    cache_key = build_cache_key(request)
    cached = get_cached(cache_key)
    if cached is not None:
        apply_cache_headers(response)
        return cached

    service = _get_service()
    candidate = service.get_candidate(global_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró candidato con Global ID: {global_id}",
        )

    set_cached(cache_key, candidate)
    apply_cache_headers(response)

    return candidate