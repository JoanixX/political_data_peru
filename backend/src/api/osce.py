import polars as pl
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from backend.src.schemas.osce import OsceCompanyResponse, OsceSanctionRecord
from src.ingestion.osce_scraper import (
    build_fup_url,
    SANCTIONS_STAGING,
    CONSORCIOS_STAGING,
)

router = APIRouter(prefix="/v1", tags=["osce"])

# path de penalidades en staging
_PENALIDADES_STAGING = Path("data/staging/osce_penalidades.parquet")

def _load_parquet_if_exists(path: Path) -> pl.DataFrame | None:
    if path.exists():
        return pl.read_parquet(str(path))
    return None

@router.get(
    "/osce/{ruc}",
    response_model=OsceCompanyResponse,
    summary="Ficha de auditoría OSCE por RUC",
    description=(
        "Consulta el historial completo de sanciones, multas, inhabilitaciones, "
        "penalidades contractuales y participación en consorcios de una empresa "
        "registrada ante OSCE. Incluye el hipervínculo directo a la Ficha Única "
        "del Proveedor (FUP) del portal oficial del Estado."
    ),
    responses={
        404: {"description": "No se encontraron registros para el RUC proporcionado"},
        503: {
            "description": "Datos de staging OSCE no disponibles. "
                           "Ejecute el pipeline de ingesta primero."
        },
    },
)
def get_osce_by_ruc(ruc: str):
    # validación básica del RUC
    ruc_clean = ruc.strip()
    if not ruc_clean.isdigit() or len(ruc_clean) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"RUC inválido: '{ruc}'. "
                "El RUC debe ser un número de exactamente 11 dígitos."
            ),
        )

    # verificar que staging existe
    if not SANCTIONS_STAGING.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El registro de sanciones OSCE no está disponible. "
                "Ejecute 'python -m src.ingestion.osce_scraper' para generar "
                "los datos de staging."
            ),
        )

    fup_url = build_fup_url(ruc_clean)
    nombre_empresa = None
    sanciones: list[OsceSanctionRecord] = []
    en_penalidades = False
    total_penalidades = 0
    en_consorcios = False
    total_consorcios = 0

    # sanciones
    sanctions_df = _load_parquet_if_exists(SANCTIONS_STAGING)
    if sanctions_df is not None:
        matched = sanctions_df.filter(pl.col("ruc") == ruc_clean)
        if len(matched) > 0:
            nombre_empresa = matched[0, "nombre_empresa"]
            for row in matched.iter_rows(named=True):
                sanciones.append(OsceSanctionRecord(
                    ruc=row["ruc"],
                    nombre_empresa=row.get("nombre_empresa"),
                    tipo_sancion=row.get("tipo_sancion"),
                    fecha_inicio=row.get("fecha_inicio"),
                    fecha_fin=row.get("fecha_fin"),
                    motivo=row.get("motivo"),
                    monto=row.get("monto"),
                    numero_resolucion=row.get("numero_resolucion"),
                ))

    
    # penalidades
    penalidades_df = _load_parquet_if_exists(_PENALIDADES_STAGING)
    if penalidades_df is not None:
        pen_matched = penalidades_df.filter(pl.col("ruc") == ruc_clean)
        total_penalidades = len(pen_matched)
        en_penalidades = total_penalidades > 0
        if en_penalidades and nombre_empresa is None:
            # intentar obtener nombre desde penalidades
            first_name = pen_matched[0, "nombre_empresa"]
            if first_name:
                nombre_empresa = first_name

    # consorcios
    consorcios_df = _load_parquet_if_exists(CONSORCIOS_STAGING)
    if consorcios_df is not None:
        cons_matched = consorcios_df.filter(
            (pl.col("ruc_consorcio") == ruc_clean)
            | (pl.col("ruc_miembro") == ruc_clean)
        )
        total_consorcios = len(cons_matched)
        en_consorcios = total_consorcios > 0

    # si no hay datos en ninguna fuente devuelve error
    if not sanciones and not en_penalidades and not en_consorcios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No se encontraron registros OSCE para RUC {ruc_clean}. "
                f"Puede verificar directamente en: {fup_url}"
            ),
        )

    return OsceCompanyResponse(
        ruc=ruc_clean,
        fup_url=fup_url,
        nombre_empresa=nombre_empresa,
        total_sanciones=len(sanciones),
        sanciones=sanciones,
        en_penalidades=en_penalidades,
        total_penalidades=total_penalidades,
        en_consorcios=en_consorcios,
        total_consorcios=total_consorcios,
    )