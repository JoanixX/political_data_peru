import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

class BaseScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_page(self, url: str):
        # se hace llamada con timeout de 30 segundos para evitar bloqueos
        # y reintentos en caso de fallos
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    # reintentos controlados para evitar bloqueos
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def post_data(self, url: str, payload: dict):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def fetch_all_candidate_data(self, id_hoja_vida: int) -> dict:
        base = "https://web.jne.gob.pe/serviciovotoinformado/api"
        endpoints = {
            "principal": f"{base}/hojavidavoto/hojavida-principal?IdHojaVida={id_hoja_vida}",
            "experiencia_laboral": f"{base}/hojavidavoto/ExperienciaLaboral?IdHojaVida={id_hoja_vida}",
            "educacion_universitaria": f"{base}/hojavidavoto/estudiosUniversitarios?IdHojaVida={id_hoja_vida}",
            "ingresos": f"{base}/hojavidavoto/ingresosvoto?IdHojaVida={id_hoja_vida}",
            "bienes_inmuebles": f"{base}/hojavidavoto/BienesInmuebles?IdHojaVida={id_hoja_vida}",
            "bienes_muebles": f"{base}/hojavidavoto/BienesMueblesvoto?IdHojaVida={id_hoja_vida}",
            "educacion_basica": f"{base}/hojavidavoto/educacionbasica?IdHojaVida={id_hoja_vida}",
            "educacion_tecnica": f"{base}/hojavidavoto/educaciontecnica?IdHojaVida={id_hoja_vida}",
            "posgrado": f"{base}/hojavidavoto/Posgradovoto?IdHojaVida={id_hoja_vida}",
            "cargo_partidario": f"{base}/hojavidavoto/cargopartidario?IdHojaVida={id_hoja_vida}",
            "info_adicional": f"{base}/hojavidavoto/Informacionadicional?IdHojaVida={id_hoja_vida}",
            "sentencia_penal": f"{base}/hojavidavoto/sentenciapenal?IdHojaVida={id_hoja_vida}",
            "sentencia_obliga": f"{base}/hojavidavoto/sentenciaobliga?IdHojaVida={id_hoja_vida}",
            "anotacion_marginal": f"https://apiplataformaelectoral3.jne.gob.pe/api/v1/candidato/anotacion-marginal?IdHojaVida={id_hoja_vida}"
        }
 
        async def safe_fetch(key, url):
            try:
                data = await self.fetch_page(url)
                return key, data
            except Exception as e:
                return key, None

        tasks = [safe_fetch(k, v) for k, v in endpoints.items()]
        results = await asyncio.gather(*tasks)
        
        consolidated = {}
        for key, data in results:
            consolidated[key] = data
            
        return consolidated