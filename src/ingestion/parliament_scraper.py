import asyncio
import json
from pathlib import Path
from src.ingestion.scrapers_base import BaseScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ParliamentScraper(BaseScraper):
    # scarper para candidatos al parlamento andino, usa concurrencia limitada
    # y resiliencia ante fallos individuales
    def __init__(self):
        super().__init__()
        self.list_url = "https://web.jne.gob.pe/serviciovotoinformado/api/candidatos/listarcandidatos"
        self.consolidated_url = "https://web.jne.gob.pe/serviciovotoinformado/api/hojavidavoto/hojavida-principal"
        self.marginal_url = "https://web.jne.gob.pe/serviciovotoinformado/api/hojavidavoto/sentenciapenal"
        self.plan_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/plangobierno"
        self.output_dir = Path("data/raw/parlamento_andino")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def get_candidate_list(self) -> list:
        # obtiene una lista mediante el post
        payload = {
            "idProcesoElectoral": 124,
            "strUbiDepartamento": "",
            "idTipoEleccion": 3
        }
        logger.info(f"Iniciando ingesta de Parlamento Andino (Proceso {payload['idProcesoElectoral']})")
        
        try:
            response = await self.post_data(self.list_url, payload)
            if isinstance(response, list):
                return response
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error crítico obteniendo lista de candidatos: {e}")
            return []

    async def scrape_candidate(self, candidate: dict, semaphore: asyncio.Semaphore):
        # orquesta la descarga y persistencia de un candidato individual
        id_hv = candidate.get("idHojaVida")
        if not id_hv:
            return False

        async with semaphore:
            try:
                # fetchea todo con el base scraper
                consolidated = await self.fetch_all_candidate_data(id_hv)

                # payload crudo
                raw_payload = {
                    "base_info": candidate,
                    "consolidated_profile": consolidated
                }

                # aqui se hace uso de la capa bronze para guardar los datos 
                #y persistirlos
                file_path = self.output_dir / f"{id_hv}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_payload, f, ensure_ascii=False, indent=4)
                
                logger.debug(f"Candidato {id_hv} persistido exitosamente.")
                return True

            except Exception as e:
                logger.error(f"Fallo en procesamiento de candidato {id_hv}: {e}")
                return False

    async def run(self):
        """Punto de entrada principal para el scraper."""
        candidates = await self.get_candidate_list()
        if not candidates:
            logger.warning("No se encontraron candidatos para procesar.")
            return

        # concurrencia controlada de 5 candidatos a la vez
        sem = asyncio.Semaphore(5)
        tasks = [self.scrape_candidate(c, sem) for c in candidates]
        
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        logger.info(f"Proceso finalizado. Exitosos: {success_count}/{len(candidates)}")