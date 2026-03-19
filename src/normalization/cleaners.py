import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

def clean_candidate_names(df: pd.DataFrame) -> pd.DataFrame:
    #limpieza básica de nombres: mayúsculas y quitar espacios extra
    logger.info("limpiando nombres de candidatos...")
    df['nombres'] = df['nombres'].str.upper().str.strip()
    return df

def standardize_dni(dni: str) -> str:
    #asegura que el dni tenga 8 digitos con ceros a la izquierda
    if not dni:
        return ""
    return str(dni).zfill(8)

def run_normalization_pipeline(raw_data_path: str):
    #ejecuta el flujo completo de normalizacion de la capa bronze a silver
    logger.info(f"procesando datos desde {raw_data_path}")
    # aca iria la logica completa con polars para alta eficiencia
    pass