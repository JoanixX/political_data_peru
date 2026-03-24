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
        self.list_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/listarCanditatos"
        self.consolidated_url = "https://web.jne.gob.pe/serviciovotoinformado/api/votoinf/HVConsolidado"
        self.marginal_url = "https://apiplataformaelectoral3.jne.gob.pe/api/v1/candidato/anotacion-marginal"
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
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error crítico obteniendo lista de candidatos: {e}")
            return []

    async def get_marginal_annotations(self, id_hoja_vida: int) -> list:
        # obtiene anotaciones marginales mediante get
        try:
            url = f"{self.marginal_url}?IdHojaVida={id_hoja_vida}"
            response = await self.fetch_page(url)
            return response.get("data", [])
        except Exception as e:
            logger.warning(f"No se pudieron obtener anotaciones para HV {id_hoja_vida}: {e}")
            return []

    async def get_consolidated_hv(self, id_hoja_vida: int) -> dict:
        # obtiene el hv consolidado mediante get
        try:
            url = f"{self.consolidated_url}?idHojaVida={id_hoja_vida}"
            response = await self.fetch_page(url)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error al obtener HV consolidado para {id_hoja_vida}: {e}")
            return {}

    async def scrape_candidate(self, candidate: dict, semaphore: asyncio.Semaphore):
        # orquesta la descarga y persistencia de un candidato individual
        id_hv = candidate.get("idHojaVida")
        if not id_hv:
            return False

        async with semaphore:
            try:
                # descargas asíncronas concurrentes por candidato
                hv_data = await self.get_consolidated_hv(id_hv)
                marginal_data = await self.get_marginal_annotations(id_hv)

                # payload crudo
                raw_payload = {
                    "base_info": candidate,
                    "hv_consolidado": hv_data,
                    "anotaciones_marginales": marginal_data
                }

                # aqui se hace uso de la capa bronze para guardar los datos y
                # persistirlos
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