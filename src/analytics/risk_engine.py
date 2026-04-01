import polars as pl
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_financial_risk(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Computando Riesgo Financiero usando MAD (Robust Z-Score)...")
    # definimos regla de cold start
    lf = lf.with_columns(
        pl.when((pl.col("ingresos_totales") == 0) & (pl.col("experiencia_publica_anios") == 0))
        .then(pl.lit(None).cast(pl.Float64))
        .otherwise(pl.col("valor_total_bienes") / (pl.col("ingresos_totales") + 1.0))
        .alias("_ratio_patrimonio")
    )
    
    # mediana y mad globales (ignora nulos)
    lf = lf.with_columns([
        pl.col("_ratio_patrimonio").median().alias("_median_patrimonio")
    ])
    
    lf = lf.with_columns([
        (pl.col("_ratio_patrimonio") - pl.col("_median_patrimonio")).abs().median().alias("_mad_patrimonio")
    ])
    
    # robust z-score
    robust_z_expr = (pl.col("_ratio_patrimonio") - pl.col("_median_patrimonio")) / (pl.col("_mad_patrimonio") * 1.4826)
    
    # mapeo a score [0, 100]
    mapped_z_score = 100.0 - pl.max_horizontal(
        pl.min_horizontal(robust_z_expr, pl.lit(3.0)), 
        pl.lit(0.0)
    ) * (100.0 / 3.0)
    
    # asignamos score final
    lf = lf.with_columns([
        pl.when(pl.col("_ratio_patrimonio").is_null())
        .then(pl.lit(50.0))
        .otherwise(
            pl.when(pl.col("_mad_patrimonio") == 0)
            .then(
                pl.when(pl.col("_ratio_patrimonio") > pl.col("_median_patrimonio"))
                .then(pl.lit(0.0))
                .otherwise(pl.lit(100.0))
            )
            .otherwise(mapped_z_score)
        ).alias("score_financiero")
    ])
    
    return lf.drop(["_ratio_patrimonio", "_median_patrimonio", "_mad_patrimonio"])

def evaluate_legal_integrity(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Computando Riesgo Legal...")
    
    # sistema de escala
    return lf.with_columns([
        pl.when(pl.col("conteo_sentencias") == 0).then(pl.lit(100.0))
        .when(pl.col("conteo_sentencias") == 1).then(pl.lit(50.0))
        .otherwise(pl.lit(0.0))
        .alias("score_legal")
    ])

def evaluate_party_stability(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Computando Estabilidad Partidaria...")
    # ratio de renuncias por años de carrera
    expr_ratio_renuncias = pl.col("cantidad_renuncias") / (pl.col("experiencia_publica_anios") + 1.0)
    
    # escala
    mapped_stability = 100.0 - (expr_ratio_renuncias * 100.0)
    
    return lf.with_columns([
        pl.max_horizontal(mapped_stability, pl.lit(0.0)).alias("score_estabilidad")
    ])

def generate_risk_flags(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Anexando Risk Flags...")
    
    return lf.with_columns(
        pl.concat_list([
            pl.when((pl.col("ingresos_totales") == 0) & (pl.col("experiencia_publica_anios") == 0))
            .then(pl.lit("Información Financiera Insuficiente"))
            .otherwise(pl.lit(None)),
            
            pl.when(pl.col("score_financiero") < 40.0)
            .then(pl.lit("Desbalance Patrimonial Detectado"))
            .otherwise(pl.lit(None)),
            
            pl.when(pl.col("conteo_sentencias") == 1)
            .then(pl.lit("Antecedente Penal/Civil Registrado"))
            .otherwise(pl.lit(None)),
            
            pl.when(pl.col("conteo_sentencias") > 1)
            .then(pl.lit("Múltiples Sentencias (Alto Riesgo Legal)"))
            .otherwise(pl.lit(None)),
            
            pl.when(pl.col("score_estabilidad") < 50.0)
            .then(pl.lit("Alta Volatilidad Partidaria (Tránsfuga)"))
            .otherwise(pl.lit(None))
        ]).list.eval(pl.element().drop_nulls()).alias("risk_flags")
    )

def synthesize_itr(lf: pl.LazyFrame) -> pl.LazyFrame:
    logger.info("Consolidando ITR con ponderación: Financiero 40%, Legal 40%, Estabilidad 20%...")
    
    return lf.with_columns([
        (
            pl.col("score_financiero") * 0.40 + 
            pl.col("score_legal") * 0.40 + 
            pl.col("score_estabilidad") * 0.20
        ).round(2).alias("score_itr")
    ])

def append_government_plans(lf: pl.LazyFrame, planes_path: str) -> pl.LazyFrame:
    logger.info(f"Anexando textos de Planes de Gobierno desde {planes_path}...")
    planes_file = Path(planes_path)
    
    if not planes_file.exists():
        logger.warning(f"Archivo de planes {planes_path} no encontrado. Se llenará con contexto en blanco.")
        return lf.with_columns(pl.lit("").alias("search_context"))
        
    planes_lf = pl.scan_parquet(str(planes_file))
    
    # suponiendo que columnas de dimensiones en el parquet de planes
    cols_to_concat = ["dimension_social", "dimension_economica", "dimension_ambiental", "dimension_institucional"]
    concat_expr = pl.concat_str([
        pl.col(c).fill_null("") for c in cols_to_concat
    ], separator=" \n ")
    
    planes_lf = planes_lf.with_columns(
        concat_expr.alias("search_context")
    ).select(["id_organizacion_politica", "search_context"])
    
    # left join porque no todos los candidatos tienen plan de gobierno
    return lf.join(planes_lf, on="id_organizacion_politica", how="left")

def extract_wide_table(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.select([
        "global_id",
        "dni",
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        "partido",
        "cargo",
        "source_category",
        
        # metricas originales
        "ingresos_totales",
        "valor_total_bienes",
        "conteo_sentencias",
        "experiencia_publica_anios",
        "cantidad_renuncias",
        
        # outputs del motor
        "score_financiero",
        "score_legal",
        "score_estabilidad",
        "score_itr",
        "risk_flags",
        "search_context"
    ])

def run_risk_engine(silver_path: str = "data/normalized/candidatos_silver.parquet", 
                    planes_path: str = "data/normalized/planes_gobierno_silver.parquet",
                    gold_path: str = "data/curated/candidates_gold.parquet"):
    silver_file = Path(silver_path)
    output_file = Path(gold_path)
    
    if not silver_file.exists():
        logger.error(f"No se encontró la capa Silver en {silver_path}.")
        return

    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Iniciando Risk Engine sobre {silver_path}...")
    
    # lazy loading
    lf = pl.scan_parquet(str(silver_file))
    lf = evaluate_financial_risk(lf)
    lf = evaluate_legal_integrity(lf)
    lf = evaluate_party_stability(lf)
    lf = synthesize_itr(lf)
    lf = generate_risk_flags(lf)
    lf = append_government_plans(lf, planes_path)
    lf = extract_wide_table(lf)
    
    logger.info("Ejecutando grafo y guardando dataset curado...")
    df_gold = lf.collect()
    
    df_gold.write_parquet(str(output_file), compression="zstd")
    
    logger.info(f"Risk Engine finalizado. Total registros orquestados: {len(df_gold)}")

if __name__ == "__main__":
    run_risk_engine()