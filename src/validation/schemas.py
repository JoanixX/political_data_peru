import polars as pl
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataQualityError(Exception):
    # creado para abortar el flujo si ocurre un error irrecuperable
    pass

class DataFramework:
    def __init__(self, reject_dir: str = "data/rejected", max_error_ratio: float = 0.2):
        self.reject_dir = Path(reject_dir)
        self.max_error_ratio = max_error_ratio

    def validate_silver_records(self, df: pl.DataFrame) -> pl.DataFrame:
        # implementa circuit breaker validando registros individuales, si uno
        # no cumple se guarda en rechazados
        total_rows = len(df)
        if total_rows == 0:
            return df
            
        logger.info(f"Iniciando validación de calidad (circuit breaker) sobre {total_rows} registros...")

        # reglas de validacion para dni valido
        valid_dni_expr = (
            pl.col("dni").is_not_null() & 
            (pl.col("dni").str.len_chars() == 8) & 
            (pl.col("dni").str.contains(r"^\d{8}$"))
        )
        
        # reglas para campos nulos criticos
        valid_nombres_expr = pl.col("nombres").is_not_null() & (pl.col("nombres").str.len_chars() > 0)
        
        # evaluacion consolidada de validez
        df_eval = df.with_columns([
            valid_dni_expr.alias("_is_dni_valid"),
            valid_nombres_expr.alias("_is_nombres_valid"),
        ])
        
        # separamos registros validos e invalidos
        df_valid = df_eval.filter(
            pl.col("_is_dni_valid") & pl.col("_is_nombres_valid")
        ).drop(["_is_dni_valid", "_is_nombres_valid"])
        
        df_invalid = df_eval.filter(
            ~pl.col("_is_dni_valid") | ~pl.col("_is_nombres_valid")
        )
        
        invalid_count = len(df_invalid)
        
        if invalid_count > 0:
            logger.warning(f"Se detectaron {invalid_count} registros inválidos. Guardando en rechazados...")
            
            df_rejected = df_invalid.with_columns(
                pl.when(~pl.col("_is_dni_valid") & ~pl.col("_is_nombres_valid"))
                .then(pl.lit("dni invalido y nombres nulos"))
                .when(~pl.col("_is_dni_valid"))
                .then(pl.lit("dni invalido (no es num o dif 8 chars)"))
                .when(~pl.col("_is_nombres_valid"))
                .then(pl.lit("campo critico nulo: nombres"))
                .otherwise(pl.lit("error desconocido"))
                .alias("motivo_rechazo")
            ).drop(["_is_dni_valid", "_is_nombres_valid"])
            
            self._save_rejected_records(df_rejected)
            
            error_ratio = invalid_count / total_rows
            if error_ratio > self.max_error_ratio:
                logger.error(f"Circuit breaker disparado: ratio de error ({error_ratio:.1%}) supera maximo ({self.max_error_ratio:.1%})")
                raise DataQualityError(f"Demasiados datos corruptos ({error_ratio:.1%}) detectados en validacion silver.")
                
        logger.info(f"Validación completa. Registros válidos retenidos: {len(df_valid)}")
        return df_valid
        
    def _save_rejected_records(self, df_rejected: pl.DataFrame) -> None:
        # guarda progresivamente los registros malos para futura inspeccion
        self.reject_dir.mkdir(parents=True, exist_ok=True)
        reject_path = self.reject_dir / "failed_records.parquet"
        
        if reject_path.exists():
            try:
                df_hist = pl.read_parquet(str(reject_path))
                # garantizamos compatibilidad de esquemas forzando columnas
                # nulas si faltaran
                for col in df_hist.columns:
                    if col not in df_rejected.columns:
                        df_rejected = df_rejected.with_columns(pl.lit(None).alias(col))
                for col in df_rejected.columns:
                    if col not in df_hist.columns:
                        df_hist = df_hist.with_columns(pl.lit(None).alias(col))
                        
                df_merged = pl.concat([df_hist, df_rejected], how="diagonal")
                df_merged.write_parquet(str(reject_path), compression="zstd")
            except Exception as e:
                logger.error(f"Error al agregar registros históricos fallidos: {e}")
                import time
                new_path = self.reject_dir / f"failed_records_{int(time.time())}.parquet"
                df_rejected.write_parquet(str(new_path), compression="zstd")
        else:
            df_rejected.write_parquet(str(reject_path), compression="zstd")