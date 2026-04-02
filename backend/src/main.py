import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.src.config.settings import settings
from backend.src.repositories.parquet_repository import ParquetRepository
from backend.src.services.candidate_service import CandidateService
from backend.src.api.candidates import router as candidates_router
from backend.src.api.health import router as health_router

logger = logging.getLogger("backend")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# instancias globales durante el lifespan
parquet_repo = ParquetRepository()
candidate_service = CandidateService(parquet_repo)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando carga del dataset Gold en memoria...")

    if parquet_repo.check_gold_exists():
        parquet_repo.load()
        logger.info(
            f"Dataset cargado: {parquet_repo.record_count} registros | ETag: {parquet_repo.etag[:16]}..."
        )
    else:
        logger.warning(
            "Archivo Gold no encontrado. El servicio arranca en modo degradado. "
            "Ejecuta el pipeline para generar data/curated/candidates_gold.parquet"
        )
    yield
    logger.info("Servidor apagándose correctamente.")

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "API REST para consulta de datos políticos curados del Perú. "
        "Expone la Capa Gold del Data Lake con soporte para paginación, "
        "caché in-memory y ETags para alta eficiencia."
    ),
    lifespan=lifespan,
)

# cors abierto para desarrollo, en prod restringimos al dominio del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates_router)
app.include_router(health_router)

@app.post(
    "/v1/admin/reload",
    tags=["administracion"],
    summary="Recarga el dataset Gold",
    description="Fuerza la recarga del archivo Parquet Gold sin reiniciar el servidor.",
)
def reload_data():
    changed = parquet_repo.reload()
    return {
        "reloaded": changed,
        "record_count": parquet_repo.record_count,
        "etag": parquet_repo.etag,
    }