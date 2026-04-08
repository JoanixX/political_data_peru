import polars as pl
from rapidfuzz import process, distance
from src.utils.logger import get_logger
from src.ingestion.osce_scraper import (
    normalize_company_name,
    load_sanctions_registry,
    load_ruc_bridge,
    build_fup_url,
)

logger = get_logger(__name__)

def _deterministic_match(
    candidates_lf: pl.LazyFrame,
    dni_col: str,
) -> pl.DataFrame:
    bridge_lf = load_ruc_bridge()
    sanctions_lf = load_sanctions_registry()

    # paso 1: dni del cantidado y el ruc de sus empresas asociadas
    cand_rucs = (
        candidates_lf
        .select([
            pl.col("global_id"),
            pl.col(dni_col).cast(pl.Utf8).str.strip_chars().alias("numero_documento"),
        ])
        .filter(pl.col("numero_documento").is_not_null())
        .join(bridge_lf, on="numero_documento", how="inner")
    )

    # paso 2: de acuerdo a los ruc se obtienen las sanciones registradas
    matches = (
        cand_rucs
        .join(
            sanctions_lf.select(["ruc", "nombre_empresa", "tipo_sancion"]).unique(),
            on="ruc",
            how="inner",
        )
        .select([
            pl.col("global_id"),
            pl.col("nombre_empresa").alias("empresa_candidato"),
            pl.col("nombre_empresa").alias("osce_sancionada_match"),
            pl.lit(1.0).alias("osce_match_score"),
            pl.col("ruc").alias("ruc_sancionado"),
            pl.col("tipo_sancion"),
            pl.lit("DETERMINISTIC").alias("osce_match_method"),
        ])
        .unique()
    )

    df = matches.collect()
    logger.info(f"Fase 1 (Determinista): {len(df)} matches DNI→RUC→Sancionado")
    return df


def _fuzzy_match(
    candidates_lf: pl.LazyFrame,
    company_col: str,
    threshold: float = 0.92,
) -> pl.DataFrame:
    sanctions_lf = load_sanctions_registry()
    cand_df = (
        candidates_lf
        .select([
            pl.col("global_id"),
            pl.col(company_col).alias("empresa_candidato"),
        ])
        .drop_nulls()
        .unique()
        .collect()
    )

    osce_df = (
        sanctions_lf
        .select(["ruc", "nombre_empresa", "nombre_empresa_norm", "tipo_sancion"])
        .unique(subset=["nombre_empresa_norm"])
        .collect()
    )

    osce_choices = osce_df["nombre_empresa_norm"].to_list()
    osce_ruc_map = dict(zip(osce_df["nombre_empresa_norm"].to_list(), osce_df["ruc"].to_list()))
    osce_name_map = dict(zip(osce_df["nombre_empresa_norm"].to_list(), osce_df["nombre_empresa"].to_list()))
    osce_type_map = dict(zip(osce_df["nombre_empresa_norm"].to_list(), osce_df["tipo_sancion"].to_list()))

    # normalizamos nombres del candidato
    cand_df = cand_df.with_columns(
        normalize_company_name(pl.col("empresa_candidato")).alias("_cand_norm")
    )

    logger.info(
        f"Fase 2 (Fuzzy): {len(cand_df)} entidades de candidatos vs "
        f"{len(osce_choices)} sancionados OSCE (umbral={threshold})"
    )

    results = []
    for row in cand_df.iter_rows(named=True):
        query_norm = row["_cand_norm"]
        if not query_norm or len(query_norm) < 3:
            continue

        match = process.extractOne(
            query_norm,
            osce_choices,
            scorer=distance.JaroWinkler.normalized_similarity,
            score_cutoff=threshold,
        )

        if match:
            best_norm, score, _ = match
            results.append({
                "global_id": row["global_id"],
                "empresa_candidato": row["empresa_candidato"],
                "osce_sancionada_match": osce_name_map[best_norm],
                "osce_match_score": score,
                "ruc_sancionado": osce_ruc_map[best_norm],
                "tipo_sancion": osce_type_map[best_norm],
                "osce_match_method": "FUZZY",
            })

    df = pl.DataFrame(results, schema={
        "global_id": pl.Utf8,
        "empresa_candidato": pl.Utf8,
        "osce_sancionada_match": pl.Utf8,
        "osce_match_score": pl.Float64,
        "ruc_sancionado": pl.Utf8,
        "tipo_sancion": pl.Utf8,
        "osce_match_method": pl.Utf8,
    })

    logger.info(f"Fase 2 (Fuzzy): {len(df)} matches de alto riesgo")
    return df

def generate_osce_match_dictionary(
    candidates_lf: pl.LazyFrame,
    threshold: float = 0.92,
    dni_col: str = "dni",
    company_col: str = "empresa_candidato",
) -> pl.DataFrame:
    schema = candidates_lf.collect_schema()
    col_names = schema.names()

    deterministic_df = pl.DataFrame(schema={
        "global_id": pl.Utf8, "empresa_candidato": pl.Utf8,
        "osce_sancionada_match": pl.Utf8, "osce_match_score": pl.Float64,
        "ruc_sancionado": pl.Utf8, "tipo_sancion": pl.Utf8,
        "osce_match_method": pl.Utf8,
    })

    if dni_col in col_names:
        deterministic_df = _deterministic_match(candidates_lf, dni_col)

    # fuzzy que se aplica solo para candidatos sin match determinista
    fuzzy_df = pl.DataFrame(schema={
        "global_id": pl.Utf8, "empresa_candidato": pl.Utf8,
        "osce_sancionada_match": pl.Utf8, "osce_match_score": pl.Float64,
        "ruc_sancionado": pl.Utf8, "tipo_sancion": pl.Utf8,
        "osce_match_method": pl.Utf8,
    })

    if company_col in col_names:
        matched_ids = set(deterministic_df["global_id"].to_list()) if len(deterministic_df) > 0 else set()
        if matched_ids:
            remaining = candidates_lf.filter(~pl.col("global_id").is_in(list(matched_ids)))
        else:
            remaining = candidates_lf
        fuzzy_df = _fuzzy_match(remaining, company_col, threshold)

    # union de las dos fases
    combined = pl.concat([deterministic_df, fuzzy_df], how="vertical_relaxed")

    if len(combined) > 0:
        combined = combined.with_columns(
            pl.col("ruc_sancionado").map_elements(
                build_fup_url, return_dtype=pl.Utf8
            ).alias("fup_url")
        )
    else:
        combined = combined.with_columns(
            pl.lit(None).cast(pl.Utf8).alias("fup_url")
        )

    logger.info(
        f"Matching OSCE finalizado: {len(combined)} coincidencias totales "
        f"({len(deterministic_df)} deterministas, {len(fuzzy_df)} fuzzy)"
    )
    return combined