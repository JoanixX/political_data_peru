import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class BaseScraper:
    def init(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_page(self, url: str):
        # se hace una llamada con varios reintentos, si el jne nos banea el script espera
        # y vuelve a reintentar después
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()