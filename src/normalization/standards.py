import uuid
import polars as pl
from src.utils.logger import get_logger

logger = get_logger(__name__)

# namespace constante para que el id se mantenga igual entre distintos 
# procesos electorales
POLITICAL_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "political_data_peru.io")

def _generate_deterministic_id(dni: str | None, nombre_completo: str | None, fecha_nacimiento: str | None) -> str:
    # quita espacios para evitar que el hash cambie
    dni_clean = str(dni).strip() if dni is not None else ""
    
    if dni_clean.isdigit() and len(dni_clean) == 8:
        # prioridad al dni
        seed = f"DNI:{dni_clean}"
    else:
        # si no hay dni valido, se usa una combinacion de nombre y 
        # fecha como fallback
        nombre_clean = str(nombre_completo).strip().upper() if nombre_completo is not None else "UNKNOWN"
        fecha_clean = str(fecha_nacimiento).strip() if fecha_nacimiento is not None else "UNKNOWN"
        seed = f"FallBack:{nombre_clean}|{fecha_clean}"
        
    return str(uuid.uuid5(POLITICAL_NAMESPACE, seed))

def apply_global_id(lf: pl.LazyFrame, 
                    col_dni: str = "dni", 
                    col_nombre: str = "nombres", 
                    col_fecha_nacimiento: str = "fecha_nacimiento",
                    output_col: str = "global_id") -> pl.LazyFrame:
    logger.info("Aplicando lógica de generación de global_id inmutable...")
    
    # inyecta nulos si las columnas no existen 
    # para evitar que el grafo de polars falle
    schema_cols = lf.collect_schema().names()
    
    struct_exprs = []
    for col_name in [col_dni, col_nombre, col_fecha_nacimiento]:
        if col_name in schema_cols:
            struct_exprs.append(pl.col(col_name))
        else:
            struct_exprs.append(pl.lit(None).alias(col_name))

    # aplica la udf fila a fila usando una estructura de polars
    return lf.with_columns(
        pl.struct(struct_exprs)
        .map_elements(
            lambda row: _generate_deterministic_id(
                row.get(col_dni),
                row.get(col_nombre),
                row.get(col_fecha_nacimiento)
            ),
            return_dtype=pl.Utf8
        )
        .alias(output_col)
    )