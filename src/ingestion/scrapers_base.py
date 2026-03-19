import requests
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BaseScraper:
    # clase base para todos los scrappers de datos politicos
    def __init__(self, name: str):
        self.name = name
        logger.info(f"scrapper de {name} listo para arrancar")

    def fetch(self, url: str):
        # aca hacemos la magia de bajar el contenido
        logger.info(f"bajando info de {url}")
        pass