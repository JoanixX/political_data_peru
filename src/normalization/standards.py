import uuid
import polars as pl
from src.utils.logger import get_logger

logger = get_logger(__name__)

# definimos un espacio de nombres dns constante para la idempotencia inter-ejecuciones
NAMESPACE_POLITICAL_PERU = uuid.uuid5(uuid.NAMESPACE_DNS, "politicaldata.pe")

def generate_global_id(dni: str, natural_key: str) -> str:
    # evaluamos integridad basica del dni
    if dni and len(dni) == 8 and dni.isdigit():
        seed = dni
    else:
        seed = natural_key
        
    # la estandarizacion fuerza la construccion de la cadena unica hash SHA-1
    return str(uuid.uuid5(NAMESPACE_POLITICAL_PERU, seed))

def apply_global_id(lf: pl.LazyFrame) -> pl.LazyFrame:
    # inyecta la lógica de generacion de identificador al grafo de polars
    return lf.with_columns(
        pl.struct(["dni", "natural_key_composite"]).map_elements(
            lambda row: generate_global_id(row["dni"], row["natural_key_composite"]),
            return_dtype=pl.Utf8
        ).alias("global_id")
    )