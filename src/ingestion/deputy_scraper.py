import asyncio
import json
from pathlib import Path
from src.ingestion.scrapers_base import BaseScraper
from src.models.entities import JNEResponse
from src.utils.logger import get_logger
import httpx
from tenacity import RetryError

logger = get_logger(__name__)

class DeputyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.list_url = "https://web.jne.gob.pe/serviciovotoinformado/api/candidatos/listarcandidatos"
        self.consolidated_url = "https://web.jne.gob.pe/serviciovotoinformado/api/hojavidavoto/hojavida-principal"
        self.extended_url = "https://web.jne.gob.pe/serviciovotoinformado/api/hojavidavoto/hojavida-principal"
        self.output_dir = Path("data/raw/diputados")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def get_candidate_list(self):
        # usa el payload de las elecciones y obtiene los datos
        payload = {
            "idProcesoElectoral": 124,
            "strUbiDepartamento": "",
            "idTipoEleccion": 15
        }
        logger.info(f"Obteniendo lista de candidatos para Proceso {payload['idProcesoElectoral']}...")
        
        # usamos el metodo heredado post_data con reintentos
        data = await self.post_data(self.list_url, payload)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def download_candidate_data(self, candidate, semaphore: asyncio.Semaphore):
        dni = candidate.get("strDocumentoIdentidad", "UNKNOWN")
        id_hv = candidate.get("idHojaVida")
        
        if not id_hv:
            logger.error(f"Candidato {dni} no tiene idHojaVida.")
            return False

        # descarga el consolidado y aplica fallback si es necesario
        async with semaphore:
            try:
                # se fetchea todo con el base scraper
                consolidated = await self.fetch_all_candidate_data(id_hv)

                # payload crudo
                raw_payload = {
                    "base_info": candidate,
                    "consolidated_profile": consolidated
                }

                # persistencia inmutable en la capa raw (bronze)
                file_path = self.output_dir / f"{dni}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_payload, f, ensure_ascii=False, indent=4)
                
                return True
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error con candidato {dni}: "
                    f"{e.response.status_code} - {e.response.text[:200]}"
                )
                return False
            
            except RetryError as e:
                original = e.last_attempt.exception()
                
                if isinstance(original, httpx.HTTPStatusError):
                    logger.error(
                        f"HTTP error con candidato {dni}: "
                        f"{original.response.status_code} - {original.response.text[:200]}"
                    )
                else:
                    logger.error(f"RetryError con candidato {dni}: {str(original)}")
                
                return False

            except Exception as e:
                logger.error(f"Error con candidato {dni}: {str(e)}")
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
        tasks = [self.download_candidate_data(c, sem) for c in candidates]
        
        results = await asyncio.gather(*tasks)
        logger.info(f"Extracción finalizada. Exitosos: {sum(results)}/{len(candidates)}")