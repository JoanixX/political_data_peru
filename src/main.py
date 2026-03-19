import sys
from src.utils.logger import get_logger
from src.normalization.cleaners import run_normalization_pipeline

logger = get_logger(__name__)

def main():
    #punto de entrada principal para el pipeline de political data perú
    logger.info("==========================================")
    logger.info("INICIANDO PIPELINE DE INTELIGENCIA POLITICA")
    logger.info("==========================================")
    
    try:
        # 1. Ingesta (simulado en esta base)
        logger.info("paso 1: iniciando ingesta de fuentes oficiales...")
        
        # 2. normalizacion
        logger.info("paso 2: iniciando limpieza y normalización...")
        run_normalization_pipeline("data/raw")
        
        # 3. resolucion de identidades
        logger.info("paso 3: ejecutando resolución de identidades...")        
        logger.info("pipeline completado exitosamente.")
        
    except Exception as e:
        logger.error(f"error crítico en el pipeline: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()