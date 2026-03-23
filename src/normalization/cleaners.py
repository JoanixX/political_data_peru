import polars as pl
from src.utils.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)

#primero buscamos los jsons
def get_json_files(path: str) -> list[str]:
    return[str(p) for p in Path(path).rglob("*.json")]

# ahora leemos los jsons como lazyframes
def read_json_files(paths: list[str]) -> list[pl.LazyFrame]:
    return [pl.scan_json(p) for p in paths]

#ahora unimos todos los lazyframes en uno solo
def union_lfs(lfs: list[pl.LazyFrame]) -> pl.LazyFrame:
    return pl.concat(lfs, how="diagonal")

# normalizacion de esquema
def normalize_schema(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Normalizando esquema...")
    
    #desanidado de estructuras jne, por ejemplo el odatosPersonales
    if "oDatosPersonales" in lf.columns:
        lf = lf.unnest("oDatosPersonales")
    if "oIngresos" in lf.columns:
        lf = lf.unnest("oIngresos")
        
    return lf.with_columns([
        pl.col("strNombres").fill_null("").alias("nombres"),
        pl.col("strDocumentoIdentidad").cast(pl.Utf8).alias("dni"),

        #ingreso base para que el pipeline lo procese
        pl.col("decRemuBrutaPublico").alias("monto") 
        if "decRemuBrutaPublico" in lf.columns 
        else pl.lit("0.0").alias("monto")
    ])

def clean_candidate_names(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns([
        pl.col("nombres")
        .str.to_uppercase()
        # limpieza de tildes
        .str.replace_all("Á", "A")
        .str.replace_all("É", "E")
        .str.replace_all("Í", "I")
        .str.replace_all("Ó", "O")
        .str.replace_all("Ú", "U")
        .str.replace_all("Ü", "U")
        #quitar caracteres especiales y normalizar espacios
        .str.replace_all(r"[^A-Z ]", " ") #deja solo letras y espacios
        .str.replace_all(r"\s+", " ") #unifica espacios múltiples
        .str.strip_chars()
        .alias("nombres")
    ])

def standardize_dni(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns([
        pl.col("dni")
        .fill_null("")
        .str.zfill(8)
        .alias("dni")
    ])

def clean_money_column(lf: pl.LazyFrame, col: str) -> pl.LazyFrame:
    return lf.with_columns([
        pl.col(col)
        .cast(pl.Utf8) #texto para el regex
        .str.replace_all(r"[^\d.,]", "") # quita los simbolos
        .str.replace_all(",", "") #quita separadores
        .cast(pl.Float64, strict=False)
        .alias(col)
    ])

def run_normalization_pipeline(raw_paths: list[str], output_path: str):
    #ejecuta el flujo completo de normalizacion de la capa bronze a silver
    logger.info(f"procesando datos desde {raw_paths}")
    
    #leemos los json
    json_files = []
    for path in raw_paths:
        json_files.extend(get_json_files(path))

    #del lazy
    lfs = read_json_files(json_files)
    lf = union_lfs(lfs)

    #normalizamos esquema
    lf = normalize_schema(lf)

    #limpiamos los datos
    lf = clean_candidate_names(lf)
    lf = standardize_dni(lf)
    lf = clean_money_column(lf, "monto")

    df = lf.collect()

    # exportamos a parquet
    df.write_parquet(
        output_path,
        compression="snappy"
    )