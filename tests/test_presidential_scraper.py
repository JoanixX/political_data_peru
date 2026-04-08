import unittest
from unittest.mock import patch, AsyncMock
import asyncio
import json
from pathlib import Path
from src.ingestion.presidential_scraper import PresidentialScraper

class TestPresidentialScraper(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.scraper = PresidentialScraper()
        self.scraper.output_dir = Path("data/test_raw/presidenciales")
        self.scraper.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self.scraper.output_dir.exists():
            shutil.rmtree("data/test_raw", ignore_errors=True)

    @patch("src.ingestion.scrapers_base.BaseScraper.post_data", new_callable=AsyncMock)
    async def test_get_candidate_list(self, mock_post):
        mock_post.return_value = [{"strDocumentoIdentidad": "12345678", "idOrganizacionPolitica": 1, "idHojaVida": 12345}]
        candidates = await self.scraper.get_candidate_list()
        self.assertEqual(len(candidates), 1)

    @patch("src.ingestion.scrapers_base.BaseScraper.fetch_all_candidate_data", new_callable=AsyncMock)
    async def test_download_candidate_data_success(self, mock_fetch_all):
        mock_fetch_all.return_value = {
            "principal": {"datoGeneral": {"nombres": "Juan", "apellidoPaterno": "Perez"}},
            "experiencia_laboral": [],
            "ingresos": []
        }
        
        id_hoja_vida = 12345
        sem = asyncio.Semaphore(1)
        
        success = await self.scraper.download_candidate_data(id_hoja_vida, sem)
        self.assertTrue(success)
        
        expected_file = self.scraper.output_dir / "12345.json"
        self.assertTrue(expected_file.exists())
        
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("consolidated_profile", data)
            self.assertEqual(data["consolidated_profile"]["principal"]["datoGeneral"]["nombres"], "Juan")

if __name__ == "__main__":
    unittest.main()