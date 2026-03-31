import polars as pl
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# mapeo de nombres de columnas de las fuentes jne al esquema silver
COLUMN_MAPPING = {
    "strDocumentoIdentidad": "dni",
    "strNombres": "nombres",
    "strCargoEleccion": "cargo",
    "strOrganizacionPolitica": "partido",
}

def standardize_single_file(path: str, category_name: str) -> pl.LazyFrame:
    lf = pl.read_json(path).lazy()
    
    try:
        schema = lf.collect_schema()
        cols = schema.names()
    except Exception as e:
        logger.warning(f"no se pudo obtener esquema de {path}: {e}")
        # devuelve lazyframe con el esquema correcto
        return pl.DataFrame({
            "dni": pl.Series(dtype=pl.Utf8),
            "nombres": pl.Series(dtype=pl.Utf8),
            "cargo": pl.Series(dtype=pl.Utf8),
            "partido": pl.Series(dtype=pl.Utf8),
            "ingresos_totales": pl.Series(dtype=pl.Float64),
            "cantidad_bienes": pl.Series(dtype=pl.Int64),
            "source_category": pl.Series(dtype=pl.Utf8)
        }).lazy()

    # desanida campos complejos
    if "oDatosPersonales" in cols:
        lf = lf.unnest("oDatosPersonales")
        cols = lf.collect_schema().names()
    if "oIngresos" in cols:
        lf = lf.unnest("oIngresos")
        cols = lf.collect_schema().names()
    exprs = []
    
    # mapea los campos al esquema unificado
    for src, tgt in COLUMN_MAPPING.items():
        if src in cols:
            exprs.append(pl.col(src).cast(pl.Utf8).alias(tgt))
        else:
            exprs.append(pl.lit(None).cast(pl.Utf8).alias(tgt))
            
    # calcula ingresos totales combinando sector publico y privado
    ingresos = []
    if "decRemuBrutaPublico" in cols:
        ingresos.append(pl.col("decRemuBrutaPublico").cast(pl.Float64, strict=False).fill_null(0.0))
    if "decRemuBrutaPrivado" in cols:
        ingresos.append(pl.col("decRemuBrutaPrivado").cast(pl.Float64, strict=False).fill_null(0.0))
        
    if ingresos:
        exprs.append(pl.sum_horizontal(ingresos).alias("ingresos_totales"))
    else:
        exprs.append(pl.lit(0.0).alias("ingresos_totales"))
        
    # cantidad de bienes, por default 0 si no se profundiza más
    exprs.append(pl.lit(0).alias("cantidad_bienes"))
    exprs.append(pl.lit(category_name).alias("source_category"))
    
    return lf.select(exprs)

def run_silver_orchestration():
    # orquesta la lectura, transformacion y deposito en parquet
    raw_dir = Path("data/raw")
    output_dir = Path("data/normalized")
    output_dir.mkdir(parents=True, exist_ok=True)
    categories = ["presidentes", "parlamento_andino", "senadores", "diputados"]
    lfs_to_concat = []
    
    for category in categories:
        category_path = raw_dir / category
        if not category_path.exists():
            logger.warning(f"La ruta {category_path} no existe. Saltando categoría.")
            continue
            
        json_files = list(category_path.rglob("*.json"))
        if not json_files:
            logger.info(f"No hay archivos en {category_path}")
            continue
            
        logger.info(f"Procesando {len(json_files)} archivo(s) para {category}...")
        for j_file in json_files:
            lf_std = standardize_single_file(str(j_file), category)
            lfs_to_concat.append(lf_std)
            
    if not lfs_to_concat:
        logger.error("No hubo archivos validos a procesar en toda la capa raw.")
        return
        
    logger.info("Generando plan de ejecución para unificar todos los lotes...")
    
    # concatena todos
    silver_lf = pl.concat(lfs_to_concat, how="vertical")
    
    # limpiezas globales sobre las columnas ya estandarizadas
    silver_lf = silver_lf.with_columns([
        pl.col("dni").fill_null("").str.zfill(8),
        pl.col("nombres").str.to_uppercase().str.strip_chars(),
        pl.col("cargo").str.to_uppercase().str.strip_chars(),
        pl.col("partido").str.to_uppercase().str.strip_chars()
    ])
    
    output_path = output_dir / "candidatos_silver.parquet"
    logger.info(f"volcando datos a {output_path} utilizando streaming con zstd...")
    
    try:
        # procesa por lotes y comprime con zstd
        silver_lf.sink_parquet(
            str(output_path),
            compression="zstd"
        )
        logger.info("Orquestacion a capa silver completada exitosamente.")
    except Exception as e:
        logger.error(f"Error durante la persistencia perezosa: {e}")
        # fallback si sink_parquet no soporta una operacion
        logger.info("Intentando persistencia forzada en memoria...")
        silver_lf.collect().write_parquet(
            str(output_path),
            compression="zstd"
        )
        logger.info("Persistencia forzada completada exitosamente.")

if __name__ == "__main__":
    run_silver_orchestration()