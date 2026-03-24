import polars as pl
from datetime import datetime
from pydantic import ValidationError
from typing import Tuple
from src.utils.logger import get_logger
from src.models.entities import Candidato

logger = get_logger(__name__)

class DataError(Exception):
    # creado para abortar el flujo cuando se incumple
    # una verificacion de negocio
    pass

class DataFramework:
    def __init__(self, null_threshold: float = 0.1, sample_size: int = 200):
        # se establecen margenes de tolerancia para evitar que
        # errores aislados boten todo el proceso masivo
        self.null_threshold = null_threshold
        self.sample_size = sample_size
        self.report = {
            "total": 0,
            "aprobados": 0,
            "descartados_dni": 0,
            "descartados_edad": 0,
            "errores_muestra_pydantic": 0
        }

    def critical_nulls(self, df: pl.DataFrame) -> None:
        # circuit breaker, si se pierden ids o nombres no se puede
        # hacer entity resolution (vincular datos de entidad en uno) luego
        total_rows = len(df)
        if total_rows == 0:
            return

        # mapeo defensivo dado que el json del jne a veces muta el
        # nombre de la id principal
        id_col = "idHojaVida" if "idHojaVida" in df.columns else "id_hoja_vida"
        nulls_id = df.select(pl.col(id_col).is_null().sum()).item() if id_col in df.columns else total_rows
        nulls_names = df.select(pl.col("nombres").is_null().sum()).item() if "nombres" in df.columns else total_rows
        ratio_id = nulls_id / total_rows
        ratio_names = nulls_names / total_rows

        # evita que insertemos miles de vacios en la db final 
        # (proteccion de integridad)
        if ratio_id > self.null_threshold:
            raise DataQualityError(f"Circuit Breaker: IDs de hoja de vida nulos ({ratio_id:.1%}) supera el umbral permitido")
        if ratio_names > self.null_threshold:
            raise DataQualityError(f"Circuit Breaker: Nombres nulos ({ratio_names:.1%}) supera el umbral permitido")

    def validate_dni(self, df: pl.DataFrame) -> Tuple[pl.DataFrame, pl.DataFrame]:
        # depura los identificadores basura (ej: 000000) o strings vacios
        # para asegurar los cruces de tablas
        if "dni" not in df.columns:
            return df, df.filter(pl.lit(False))

        # aplicamos una regla tajante, la de 8 caracteres exclusivamente numericos
        valid_mask = (
            pl.col("dni").is_not_null() & 
            (pl.col("dni").str.len_chars() == 8) & 
            (pl.col("dni").str.contains(r"^\d{8}$"))
        )
        
        df_valid = df.filter(valid_mask)
        df_invalid = df.filter(~valid_mask)
        
        self.report["descartados_dni"] = len(df_invalid)
        return df_valid, df_invalid

    def validate_age(self, df: pl.DataFrame) -> Tuple[pl.DataFrame, pl.DataFrame]:
        # limpia la data de errores de tipeo comunes en reniec 
        # (gente nacida en 1800 o en 2025)
        date_col = "fecha_nacimiento" if "fecha_nacimiento" in df.columns else "strFechaNacimiento"
        
        if date_col not in df.columns:
            return df, df.filter(pl.lit(False))

        current_year = datetime.now().year
        
        # usa regex para aislar el año de 4 digitos sin pelear 
        # con formatos latino/anglo de dias y meses
        df_eval = df.with_columns(
            pl.col(date_col)
            .str.extract(r"((?:19|20)\d{2})")
            .cast(pl.Int32, strict=False)
            .alias("_year_ext")
        )

        valid_mask = (
            pl.col("_year_ext").is_not_null() & 
            ((current_year - pl.col("_year_ext")) >= 18) &
            ((current_year - pl.col("_year_ext")) <= 100)
        )
        
        df_valid = df_eval.filter(valid_mask).drop("_year_ext")
        df_invalid = df_eval.filter(~valid_mask).drop("_year_ext")
        
        self.report["descartados_edad"] = len(df_invalid)
        return df_valid, df_invalid

    def validate_sample_types(self, df: pl.DataFrame) -> None:
        # toma un sample estadistico para validar cast de tipos con 
        # pydantic y con complejidad de O(1)
        if len(df) == 0:
            return
            
        n_sample = min(self.sample_size, len(df))
        sample_dicts = df.sample(n=n_sample).to_dicts()
        
        errors = 0
        for row in sample_dicts:
            try:
                # inyecta alias estandarizados para que pydantic 
                # valide el dominio puro
                mapped_row = {
                    "id_hoja_vida": row.get("id_hoja_vida", row.get("idHojaVida", 0)),
                    "dni": str(row.get("dni", "")),
                    "nombres": str(row.get("nombres", "")),
                    "apellido_paterno": str(row.get("apellido_paterno", row.get("strApellidoPaterno", ""))),
                    "apellido_materno": str(row.get("apellido_materno", row.get("strApellidoMaterno", ""))),
                    "partido": str(row.get("partido", row.get("strOrganizacionPolitica", ""))),
                    "cargo_postulacion": str(row.get("cargo_postulacion", row.get("strCargoEleccion", ""))),
                    "total_ingresos": float(row.get("monto", 0.0)),
                }
                Candidato(**mapped_row)
            except ValidationError as e:
                errors += 1
                logger.debug(f"Error de coerción de pydantic en muestra random: {e}")

        self.report["errores_muestra_pydantic"] = errors
        
        # levanta el circuit breaker 
        # si el schema drift es insalvable en produccion
        if errors > (n_sample * 0.2):
            raise DataQualityError(f"Circuit Breaker: Demasiados errores forzando tipos en la muestra ({errors}/{n_sample})")

    def validate_silver_layer(self, df: pl.DataFrame) -> pl.DataFrame:
        # orquesta el chequeo secuencial del dataframe
        logger.info("Iniciando test de integridad en la dataframe silver path...")
        self.report["total"] = len(df)

        #circuit breaker obligatorio (nulidad critica)
        self._check_critical_nulls(df)

        #dropeamos dnis imposibles
        df_clean, _ = self._validate_dni(df)
        
        # dropeamos edades imposibles
        df_clean, _ = self._validate_age(df_clean)

        # chequeamos que los tipos sean correctos
        self._validate_sample_types(df_clean)
        self.report["aprobados"] = len(df_clean)
        self._log_report()

        return df_clean

    def _log_report(self):
        total = self.report["total"]
        aprobados = self.report["aprobados"]
        tasa = (aprobados / total * 100) if total > 0 else 0
        
        logger.info("Reporte de Data Quality")
        logger.info(f"Evaluados: {total}")
        logger.info(f"Aprobados: {aprobados} ({tasa:.1f}%)")
        logger.info(f"Descartados [dni invalido]: {self.report['descartados_dni']}")
        logger.info(f"Descartados [fecha limite fallada]: {self.report['descartados_edad']}")
        logger.info(f"Fallos pydantic (muestra {self.sample_size}): {self.report['errores_muestra_pydantic']}")