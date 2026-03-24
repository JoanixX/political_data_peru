import asyncio
import json
from pathlib import Path
from src.ingestion.scrapers_base import BaseScraper
from src.models.entities import JNEResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PresidentialScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.list_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/listarCanditatos"
        self.consolidated_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/HVConsolidado"
        self.extended_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/hojavida"
        self.output_dir = Path("data/raw/presidenciales")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def get_candidate_list(self):
        # usa el payload de las elecciones y obtiene los datos
        payload = {
            "idProcesoElectoral": 124,
            "strUbiDepartamento": "",
            "idTipoEleccion": 1
        }
        logger.info(f"Obteniendo lista de candidatos para Proceso {payload['idProcesoElectoral']}...")
        
        # usamos el metodo heredado post_data con reintentos
        data = await self.post_data(self.list_url, payload)
        return data.get("data", [])

    async def download_candidate_data(self, id_hoja_vida: int, semaphore: asyncio.Semaphore):
        # descarga el consolidado y aplica fallback si es necesario
        async with semaphore:
            try:
                # 1. Intenta el HVConsolidado
                url = f"{self.consolidated_url}?idHojaVida={id_hoja_vida}"
                raw_json = await self.fetch_page(url)
                
                # valida con el pydantic
                validated_resp = JNEResponse(**raw_json)
                
                # si algo está mal o hay data vacia, se va al link extendido
                if not validated_resp.success or not validated_resp.data:
                    logger.warning(f"ID {id_hoja_vida} incompleto. Gatillando fallback extendido...")
                    ext_url = f"{self.extended_url}?idHojaVida={id_hoja_vida}"
                    extended_json = await self.fetch_page(ext_url)
                    raw_json["extended_data_fallback"] = extended_json

                # persistencia inmutable en la capa raw (bronze)
                file_path = self.output_dir / f"{id_hoja_vida}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_json, f, ensure_ascii=False, indent=4)
                
                return True
            except Exception as e:
                logger.error(f"Error con candidato {id_hoja_vida}: {str(e)}")
                return False

    async def run(self):
        # orquestador asincrono
        candidates = await self.get_candidate_list()
        if not candidates:
            logger.error("No se pudo obtener la lista de candidatos.")
            return

        # Sempahore hace el stop en 5 para no saturar el api
        # y evitar bloqueos de IP
        sem = asyncio.Semaphore(5)
        tasks = [self.download_candidate_data(c["idHojaVida"], sem) for c in candidates]
        
        results = await asyncio.gather(*tasks)
        logger.info(f"Extracción finalizada. Exitosos: {sum(results)}/{len(candidates)}")