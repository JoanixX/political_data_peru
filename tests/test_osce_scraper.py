import unittest
from unittest.mock import patch, MagicMock
import polars as pl
from pathlib import Path
import os
from src.ingestion.osce_scraper import ingest_sancionados, ingest_penalidades

class TestOsceScraper(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("data/test_raw/osce")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree("data/test_raw/osce", ignore_errors=True)

    @patch("src.ingestion.osce_scraper.OSCE_RAW_DIR")
    def test_ingest_sancionados_empty(self, mock_dir):
        mock_dir.__truediv__.return_value.exists.return_value = False
        lf = ingest_sancionados()
        df = lf.collect()
        self.assertEqual(len(df), 0)

    def test_ingest_sancionados_with_data(self):
        csv_path = self.test_dir / "sancionados.csv"
        csv_content = "RUC|NOMBRE_RAZONODENOMINACIONSOCIAL|FECHA_INICIO|FECHA_FIN|DE_MOTIVO_INFRACCION|NUMERO_RESOLUCION\n" \
                      "20100047218|EMPRESA TEST|2023-01-01|2023-12-31|MOTIVO|RES-001"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        
        with patch("src.ingestion.osce_scraper.OSCE_RAW_DIR", self.test_dir):
            lf = ingest_sancionados()
            df = lf.collect()
            self.assertEqual(len(df), 1)
            self.assertEqual(df[0, "ruc"], "20100047218")
            self.assertEqual(df[0, "nombre_empresa_norm"], "EMPRESA TEST")

if __name__ == "__main__":
    unittest.main()