from datetime import datetime, timezone
from pathlib import Path
import polars as pl
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ruta por defecto del log de auditoria
DEFAULT_AUDIT_PATH = "data/curated/audit_log.parquet"

def log_changes(
    old_df: pl.DataFrame,
    new_df: pl.DataFrame,
    key_col: str = "global_id",
    audit_path: str = DEFAULT_AUDIT_PATH,
) -> int:
    if old_df.is_empty() or new_df.is_empty():
        logger.info("Uno de los datasets esta vacio, no hay cambios que auditar.")
        return 0

    # solo comparamos registros que existan en ambas versiones
    common_keys = set(old_df[key_col].to_list()) & set(new_df[key_col].to_list())
    if not common_keys:
        logger.info("No hay registros comunes entre las dos versiones, saltando auditoria.")
        return 0

    # filtramos solo los registros comunes
    old_filtered = old_df.filter(pl.col(key_col).is_in(list(common_keys)))
    new_filtered = new_df.filter(pl.col(key_col).is_in(list(common_keys)))

    # ordenamos por clave
    old_sorted = old_filtered.sort(key_col)
    new_sorted = new_filtered.sort(key_col)

    skip_cols = {key_col, "risk_flags", "search_context"}
    compare_cols = [
        c for c in old_sorted.columns
        if c in new_sorted.columns and c not in skip_cols
    ]
    if not compare_cols:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat()
    change_entries: list[dict] = []

    old_aliased = old_sorted.select(
        [pl.col(key_col)] + [pl.col(c).alias(f"old_{c}") for c in compare_cols]
    )
    new_aliased = new_sorted.select(
        [pl.col(key_col)] + [pl.col(c).alias(f"new_{c}") for c in compare_cols]
    )
    joined = old_aliased.join(new_aliased, on=key_col, how="inner")

    # para cada columna, detectamos donde old != new
    for col in compare_cols:
        old_col = f"old_{col}"
        new_col = f"new_{col}"

        # casteamos a string para comparacion uniforme y manejo de nulos
        diff_df = joined.filter(
            pl.col(old_col).cast(pl.Utf8).fill_null("__NULL__")
            != pl.col(new_col).cast(pl.Utf8).fill_null("__NULL__")
        ).select([
            pl.col(key_col),
            pl.lit(col).alias("field_changed"),
            pl.col(old_col).cast(pl.Utf8).alias("old_value"),
            pl.col(new_col).cast(pl.Utf8).alias("new_value"),
            pl.lit(timestamp).alias("timestamp"),
        ])

        if not diff_df.is_empty():
            change_entries.append(diff_df)

    if not change_entries:
        logger.info("No se detectaron cambios entre las versiones.")
        return 0

    audit_df = pl.concat(change_entries)
    total_changes = len(audit_df)
    logger.info(f"Auditoria: {total_changes} cambio(s) detectado(s) en {len(compare_cols)} campo(s).")

    # persistimos en modo append
    output_path = Path(audit_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        existing = pl.read_parquet(str(output_path))
        audit_df = pl.concat([existing, audit_df])

    audit_df.write_parquet(str(output_path), compression="zstd")
    logger.info(f"Log de auditoria actualizado en {audit_path}.")

    return total_changes