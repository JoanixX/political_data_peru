import polars as pl
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

OSCE_RAW_DIR = Path("data/raw/osce")
STAGING_DIR = Path("data/staging")
SANCTIONS_STAGING = STAGING_DIR / "osce_sanctions_registry.parquet"
RUC_BRIDGE_STAGING = STAGING_DIR / "osce_ruc_bridge.parquet"
CONSORCIOS_STAGING = STAGING_DIR / "osce_consorcios.parquet"
FUP_BASE_URL = "https://apps.osce.gob.pe/perfilprov-ui/ficha"

def build_fup_url(ruc: str) -> str:
    return f"{FUP_BASE_URL}/{ruc}"

def normalize_company_name(name_expr: pl.Expr) -> pl.Expr:
    return (
        name_expr
        .str.to_uppercase()
        .str.replace_all(r"[\.,;]", "")
        .str.replace_all(r"\b(SAC|SA|EIRL|SRL|SRLTDA|S C R L|SCRL)\b", "")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
    )

def _pad_ruc(ruc_expr: pl.Expr) -> pl.Expr:
    return (
        ruc_expr
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.replace_all(r"[^\d]", "")
        .str.zfill(11)
    )

def ingest_sancionados() -> pl.LazyFrame:
    frames = []
    
    path_sanc = OSCE_RAW_DIR / "sancionados.csv"
    if path_sanc.exists():
        lf = pl.scan_csv(str(path_sanc), separator="|", ignore_errors=True, encoding="utf8-lossy")
        lf = lf.select([
            _pad_ruc(pl.col("RUC")).alias("ruc"),
            pl.col("NOMBRE_RAZONODENOMINACIONSOCIAL").alias("nombre_empresa"),
            pl.lit("INHABILITACION").alias("tipo_sancion"),
            pl.col("FECHA_INICIO").alias("fecha_inicio"),
            pl.col("FECHA_FIN").alias("fecha_fin"),
            pl.col("DE_MOTIVO_INFRACCION").alias("motivo"),
            pl.lit(None).cast(pl.Float64).alias("monto"),
            pl.col("NUMERO_RESOLUCION").alias("numero_resolucion"),
        ])
        frames.append(lf)
        logger.info(f"Cargado sancionados.csv")
    else:
        logger.warning(f"No encontrado: {path_sanc}")

    path_multa = OSCE_RAW_DIR / "sancionados_multa.csv"
    if path_multa.exists():
        lf = pl.scan_csv(str(path_multa), separator="|", ignore_errors=True, encoding="utf8-lossy")
        lf = lf.select([
            _pad_ruc(pl.col("RUC")).alias("ruc"),
            pl.col("NOMBRE_RAZONODENOMINACIONSOCIAL").alias("nombre_empresa"),
            pl.lit("MULTA").alias("tipo_sancion"),
            pl.col("FECHA_INICIO").alias("fecha_inicio"),
            pl.col("FECHA_FIN").alias("fecha_fin"),
            pl.col("DE_MOTIVO_INFRACCION").alias("motivo"),
            pl.col("MONTO").cast(pl.Float64, strict=False).alias("monto"),
            pl.col("NUMERO_RESOLUCION").alias("numero_resolucion"),
        ])
        frames.append(lf)
        logger.info(f"Cargado sancionados_multa.csv")
    else:
        logger.warning(f"No encontrado: {path_multa}")

    # inhabilitaciones_judiciales.csv
    path_inhab = OSCE_RAW_DIR / "inhabilitaciones_judiciales.csv"
    if path_inhab.exists():
        lf = pl.scan_csv(str(path_inhab), separator="|", ignore_errors=True, encoding="utf8-lossy")
        lf = lf.select([
            _pad_ruc(pl.col("RUC_DNI")).alias("ruc"),
            pl.col("NOMBRE_RAZONODENOMINACIONSOCIAL").alias("nombre_empresa"),
            pl.lit("INHABILITACION_JUDICIAL").alias("tipo_sancion"),
            pl.col("FECHA_INICIO").alias("fecha_inicio"),
            pl.col("FECHA_FIN").alias("fecha_fin"),
            pl.lit(None).cast(pl.Utf8).alias("motivo"),
            pl.lit(None).cast(pl.Float64).alias("monto"),
            pl.col("NUMERO_RESOLUCION").alias("numero_resolucion"),
        ])
        frames.append(lf)
        logger.info(f"Cargado inhabilitaciones_judiciales.csv")
    else:
        logger.warning(f"No encontrado: {path_inhab}")

    if not frames:
        logger.error("No se encontró ningún CSV de sanciones. Retornando frame vacío.")
        return pl.DataFrame(schema={
            "ruc": pl.Utf8, "nombre_empresa": pl.Utf8,
            "nombre_empresa_norm": pl.Utf8, "tipo_sancion": pl.Utf8,
            "fecha_inicio": pl.Utf8, "fecha_fin": pl.Utf8,
            "motivo": pl.Utf8, "monto": pl.Float64,
            "numero_resolucion": pl.Utf8,
        }).lazy()

    unified = pl.concat(frames, how="vertical_relaxed")

    # normalización de nombre + filtrado de nulos
    unified = (
        unified
        .filter(pl.col("nombre_empresa").is_not_null())
        .with_columns(
            normalize_company_name(pl.col("nombre_empresa")).alias("nombre_empresa_norm")
        )
    )
    logger.info("Sanciones unificadas correctamente.")
    return unified


def ingest_penalidades() -> pl.LazyFrame:
    path = OSCE_RAW_DIR / "penalidades.csv"
    if not path.exists():
        logger.warning(f"No encontrado: {path}")
        return pl.DataFrame(schema={
            "ruc": pl.Utf8, "nombre_empresa": pl.Utf8,
            "nombre_empresa_norm": pl.Utf8, "tipo_penalidad": pl.Utf8,
            "entidad_contratante": pl.Utf8, "fecha_penalidad": pl.Utf8,
            "descripcion": pl.Utf8, "monto": pl.Float64,
        }).lazy()

    lf = pl.scan_csv(
        str(path), separator="|", ignore_errors=True,
        encoding="utf8-lossy", truncate_ragged_lines=True,
        infer_schema_length=10000, quote_char=None,
    )
    lf = lf.rename({
        "RUC CONTRATISTA": "ruc_raw",
        "TIPO PENALIDAD": "tipo_penalidad",
        "OBJETO CONTRATO": "entidad_contratante",
        "ENTIDAD CONTRATANTE": "entidad_contratante_real",
        "FECHA PENALIDAD": "fecha_penalidad",
        "DESCRIPCION/MOTIVO": "descripcion",
        "MONTO": "monto_raw",
    })
    lf = lf.select([
        _pad_ruc(pl.col("ruc_raw")).alias("ruc"),
        pl.lit(None).cast(pl.Utf8).alias("nombre_empresa"),
        pl.col("tipo_penalidad"),
        pl.col("entidad_contratante_real").alias("entidad_contratante"),
        pl.col("fecha_penalidad"),
        pl.col("descripcion"),
        pl.col("monto_raw").cast(pl.Float64, strict=False).alias("monto"),
    ]).with_columns(
        normalize_company_name(
            pl.col("nombre_empresa").fill_null(pl.lit(""))
        ).alias("nombre_empresa_norm")
    )

    logger.info("Cargado penalidades.csv")
    return lf

def ingest_consorcios() -> pl.LazyFrame:
    xlsx_files = sorted(OSCE_RAW_DIR.glob("CONOSCE_CONSORCIO*.xlsx"))

    if not xlsx_files:
        logger.warning("No se encontraron archivos XLSX de consorcios.")
        return pl.DataFrame(schema={
            "anio": pl.Int64, "ruc_consorcio": pl.Utf8,
            "consorcio": pl.Utf8, "ruc_miembro": pl.Utf8,
            "miembro": pl.Utf8,
        }).lazy()

    frames = []
    for xlsx_path in xlsx_files:
        try:
            df = pl.read_excel(str(xlsx_path), engine="openpyxl")
            # normalizar nombres de columnas a minúsculas
            df = df.rename({c: c.lower().strip() for c in df.columns})
            df = df.select([
                pl.col("año").cast(pl.Int64, strict=False).alias("anio"),
                _pad_ruc(pl.col("ruc_consorcio")).alias("ruc_consorcio"),
                pl.col("consorcio").cast(pl.Utf8),
                _pad_ruc(pl.col("ruc_miembro")).alias("ruc_miembro"),
                pl.col("miembro").cast(pl.Utf8),
            ])
            frames.append(df.lazy())
            logger.info(f"Cargado {xlsx_path.name}: {len(df)} filas")
        except Exception as e:
            logger.error(f"Error al leer {xlsx_path.name}: {e}")

    if not frames:
        return pl.DataFrame(schema={
            "anio": pl.Int64, "ruc_consorcio": pl.Utf8,
            "consorcio": pl.Utf8, "ruc_miembro": pl.Utf8,
            "miembro": pl.Utf8,
        }).lazy()

    return pl.concat(frames, how="vertical_relaxed")


def ingest_conformacion_juridica() -> pl.LazyFrame:
    path = OSCE_RAW_DIR / "conformacion_juridica.csv"
    if not path.exists():
        logger.warning(f"No encontrado: {path}")
        return pl.DataFrame(schema={
            "numero_documento": pl.Utf8,
            "ruc": pl.Utf8,
            "nombre_empresa": pl.Utf8,
        }).lazy()

    lf = pl.scan_csv(str(path), separator="|", ignore_errors=True, encoding="utf8-lossy")
    lf = lf.select([
        pl.col("NUMERO_DOCUMENTO").cast(pl.Utf8).str.strip_chars().alias("numero_documento"),
        _pad_ruc(pl.col("RUC")).alias("ruc"),
        pl.col("NOMBRE_RAZONODENOMINACIONSOCIAL").alias("nombre_empresa"),
    ]).filter(
        pl.col("numero_documento").is_not_null()
        & pl.col("ruc").is_not_null()
    ).unique(subset=["numero_documento", "ruc"])

    logger.info("Preparado conformacion_juridica.csv (lazy, solo columnas DNI/RUC)")
    return lf

def build_osce_unified_dataset() -> tuple[pl.LazyFrame, pl.LazyFrame]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # sanciones unificadas
    sanctions_lf = ingest_sancionados()
    logger.info(f"Persistiendo registro de sanciones en {SANCTIONS_STAGING}")
    sanctions_lf.sink_parquet(str(SANCTIONS_STAGING))
    sanctions_lf = pl.scan_parquet(str(SANCTIONS_STAGING))

    # tabla puente entre el dni y el RUC
    bridge_lf = ingest_conformacion_juridica()
    logger.info(f"Persistiendo tabla puente DNI↔RUC en {RUC_BRIDGE_STAGING}")
    bridge_lf.sink_parquet(str(RUC_BRIDGE_STAGING))
    bridge_lf = pl.scan_parquet(str(RUC_BRIDGE_STAGING))

    # consorcios
    consorcios_lf = ingest_consorcios()
    logger.info(f"Persistiendo consorcios en {CONSORCIOS_STAGING}")
    consorcios_lf.sink_parquet(str(CONSORCIOS_STAGING))

    # penalidades
    penalidades_lf = ingest_penalidades()
    penalidades_staging = STAGING_DIR / "osce_penalidades.parquet"
    logger.info(f"Persistiendo penalidades en {penalidades_staging}")
    penalidades_lf.sink_parquet(str(penalidades_staging))

    logger.info("Build OSCE unificado completado.")
    return sanctions_lf, bridge_lf

def load_sanctions_registry() -> pl.LazyFrame:
    if SANCTIONS_STAGING.exists():
        return pl.scan_parquet(str(SANCTIONS_STAGING))
    logger.warning("Staging de sanciones no encontrado. Reconstruyendo...")
    sanctions_lf, _ = build_osce_unified_dataset()
    return sanctions_lf

def load_ruc_bridge() -> pl.LazyFrame:
    if RUC_BRIDGE_STAGING.exists():
        return pl.scan_parquet(str(RUC_BRIDGE_STAGING))
    logger.warning("Staging de tabla puente DNI↔RUC no encontrado. Reconstruyendo...")
    _, bridge_lf = build_osce_unified_dataset()
    return bridge_lf


if __name__ == "__main__":
    sanctions, bridge = build_osce_unified_dataset()
    s_df = sanctions.collect()
    b_df = bridge.collect()
    logger.info(f"Sanciones: {len(s_df)} registros")
    logger.info(f"Tabla puente DNI↔RUC: {len(b_df)} registros")
    logger.info("Módulo osce_scraper ejecutado exitosamente.")