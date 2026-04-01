import polars as pl
from pathlib import Path
from src.utils.logger import get_logger
import src.normalization.cleaners as cleaners
from src.validation.schemas import DataFramework
from src.normalization.standards import apply_global_id

logger = get_logger(__name__)

# mapeo de nombres de columnas de las fuentes jne al esquema silver
COLUMN_MAPPING = {
    "strDocumentoIdentidad": "dni",
    "strNombres": "nombres",
    "strApellidoPaterno": "apellido_paterno",
    "strApellidoMaterno": "apellido_materno",
    "strFechaNacimiento": "fecha_nacimiento",
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
        # devuelve lazyframe con el esquema correcto expandido
        return pl.DataFrame({
            "dni": pl.Series(dtype=pl.Utf8),
            "nombres": pl.Series(dtype=pl.Utf8),
            "apellido_paterno": pl.Series(dtype=pl.Utf8),
            "apellido_materno": pl.Series(dtype=pl.Utf8),
            "fecha_nacimiento": pl.Series(dtype=pl.Utf8),
            "cargo": pl.Series(dtype=pl.Utf8),
            "partido": pl.Series(dtype=pl.Utf8),
            "ingresos_totales": pl.Series(dtype=pl.Float64),
            "cantidad_bienes": pl.Series(dtype=pl.Int64),
            "valor_total_bienes": pl.Series(dtype=pl.Float64),
            "conteo_sentencias": pl.Series(dtype=pl.Int64),
            "experiencia_publica_anios": pl.Series(dtype=pl.Int64),
            "cantidad_renuncias": pl.Series(dtype=pl.Int64),
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
        ingresos.append(cleaners.clean_financial_column("decRemuBrutaPublico"))
    if "decRemuBrutaPrivado" in cols:
        ingresos.append(cleaners.clean_financial_column("decRemuBrutaPrivado"))
        
    if ingresos:
        exprs.append(pl.sum_horizontal(ingresos).alias("ingresos_totales"))
    else:
        exprs.append(pl.lit(0.0).alias("ingresos_totales"))
        
    # extracción y cálculo de métricas patrimoniales, legales y de carrera
    bienes_inmuebles = cleaners.sum_list_field("lBienInmueble", "decValor") if "lBienInmueble" in cols else pl.lit(0.0)
    bienes_inmuebles_autovaluo = cleaners.sum_list_field("lBienInmueble", "decAutovaluo") if "lBienInmueble" in cols else pl.lit(0.0)
    bienes_muebles = cleaners.sum_list_field("lBienMueble", "decValor") if "lBienMueble" in cols else pl.lit(0.0)
    
    exprs.append(
        pl.sum_horizontal([bienes_inmuebles, bienes_inmuebles_autovaluo, bienes_muebles])
        .alias("valor_total_bienes")
    )
    
    c_bienes_inm = cleaners.count_list_records("lBienInmueble") if "lBienInmueble" in cols else pl.lit(0)
    c_bienes_mueb = cleaners.count_list_records("lBienMueble") if "lBienMueble" in cols else pl.lit(0)
    exprs.append(pl.sum_horizontal([c_bienes_inm, c_bienes_mueb]).alias("cantidad_bienes"))
    sentencias_penales = cleaners.count_list_records("lSentenciaPenal") if "lSentenciaPenal" in cols else pl.lit(0)
    sentencias_obliga = cleaners.count_list_records("lSentenciaObliga") if "lSentenciaObliga" in cols else pl.lit(0)
    exprs.append(pl.sum_horizontal([sentencias_penales, sentencias_obliga]).alias("conteo_sentencias"))
    
    if "lExperienciaLaboral" in cols:
        exprs.append(cleaners.calculate_public_experience("lExperienciaLaboral").alias("experiencia_publica_anios"))
    else:
        exprs.append(pl.lit(0).alias("experiencia_publica_anios"))

    if "lRenunciaOP" in cols:
        exprs.append(cleaners.count_list_records("lRenunciaOP").alias("cantidad_renuncias"))
    else:
        exprs.append(pl.lit(0).alias("cantidad_renuncias"))
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
            continue
            
        json_files = list(category_path.rglob("*.json"))
        if not json_files:
            continue
            
        logger.info(f"Procesando {len(json_files)} archivo(s) para {category}...")
        for j_file in json_files:
            lf_std = standardize_single_file(str(j_file), category)
            lfs_to_concat.append(lf_std)
            
    if not lfs_to_concat:
        logger.error("No hubo archivos validos a procesar en toda la capa raw.")
        return
        
    logger.info("Generando plan de ejecución para unificar todos los lotes...")
    silver_lf = pl.concat(lfs_to_concat, how="vertical")
    
    # limpiezas globales sobre las columnas ya estandarizadas
    # conservamos internamente su formato limpio para armar el hash correcto
    silver_lf = silver_lf.with_columns([
        cleaners.normalize_identity("dni").alias("dni"),
        cleaners.standardize_text("nombres", casing="none").str.to_lowercase().alias("_nombres_flat"),
        cleaners.standardize_text("apellido_paterno", casing="none").str.to_lowercase().alias("_paterno_flat"),
        cleaners.standardize_text("apellido_materno", casing="none").str.to_lowercase().alias("_materno_flat"),
        pl.col("fecha_nacimiento").cast(pl.Utf8).fill_null("").str.strip_chars().alias("_nacimiento_flat")
    ])

    # creamos variable temporal
    silver_lf = silver_lf.with_columns([
        pl.concat_str([
            pl.col("_nombres_flat"),
            pl.col("_paterno_flat"),
            pl.col("_materno_flat"),
            pl.col("_nacimiento_flat")
        ], separator="|").alias("natural_key_composite")
    ])

    # generamos identificador global
    logger.info("Generando generador de identidad determinista (UUID v5)...")
    silver_lf = apply_global_id(silver_lf)

    # descartamos variables auxiliares y aplicamos tipografia visual
    silver_lf = silver_lf.with_columns([
        pl.col("_nombres_flat").str.to_titlecase().alias("nombres"),
        pl.col("_paterno_flat").str.to_titlecase().alias("apellido_paterno"),
        pl.col("_materno_flat").str.to_titlecase().alias("apellido_materno"),
        cleaners.standardize_text("cargo", casing="title").alias("cargo"),
        cleaners.standardize_text("partido", casing="title").alias("partido")
    ]).drop(["_nombres_flat", "_paterno_flat", "_materno_flat", "_nacimiento_flat", "natural_key_composite"])
    
    # fuerza resolucion para filtrar calidad
    logger.info("Ejecutando plan y validando calidad de registros (circuit breaker)...")
    silver_df = silver_lf.collect()
    
    validator = DataFramework()
    valid_df = validator.validate_silver_records(silver_df)
    
    output_path = output_dir / "candidatos_silver.parquet"
    logger.info(f"Volcando datos limpios y filtrados a {output_path} (zstd) con UUIDs resolutivos...")
    
    valid_df.write_parquet(
        str(output_path),
        compression="zstd"
    )
    logger.info("Orquestación y limpieza completada exitosamente.")

if __name__ == "__main__":
    run_silver_orchestration()