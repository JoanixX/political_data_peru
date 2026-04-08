"""Smoke tests for the OSCE ingestion refactoring - writes to file."""
import sys

LOG_FILE = "test_results.log"

class Logger:
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
    def log(self, msg):
        self.f.write(msg + "\n")
        self.f.flush()
        print(msg)
    def close(self):
        self.f.close()

def test_fup_url(log):
    from src.ingestion.osce_scraper import build_fup_url
    url = build_fup_url("20100047218")
    expected = "https://apps.osce.gob.pe/perfilprov-ui/ficha/20100047218"
    assert url == expected, f"URL mismatch: {url}"
    log.log(f"  FUP URL: {url}")

def test_sancionados(log):
    from src.ingestion.osce_scraper import ingest_sancionados
    lf = ingest_sancionados()
    df = lf.collect()
    assert len(df) > 0, "No se cargaron sanciones"
    assert "ruc" in df.columns
    assert "nombre_empresa_norm" in df.columns
    tipos = df["tipo_sancion"].unique().to_list()
    log.log(f"  Sanciones: {len(df)} filas, tipos: {tipos}")

def test_penalidades(log):
    from src.ingestion.osce_scraper import ingest_penalidades
    lf = ingest_penalidades()
    df = lf.collect()
    assert "ruc" in df.columns
    log.log(f"  Penalidades: {len(df)} filas")

def test_consorcios(log):
    from src.ingestion.osce_scraper import ingest_consorcios
    lf = ingest_consorcios()
    df = lf.collect()
    assert "ruc_consorcio" in df.columns
    assert "ruc_miembro" in df.columns
    log.log(f"  Consorcios: {len(df)} filas")

def test_conformacion(log):
    from src.ingestion.osce_scraper import ingest_conformacion_juridica
    lf = ingest_conformacion_juridica()
    df = lf.head(5).collect()
    assert "numero_documento" in df.columns
    assert "ruc" in df.columns
    log.log(f"  Conformacion: schema OK, columns={df.columns}")

def test_build_unified(log):
    from src.ingestion.osce_scraper import build_osce_unified_dataset
    from pathlib import Path
    sanctions_lf, bridge_lf = build_osce_unified_dataset()
    s_df = sanctions_lf.collect()
    assert len(s_df) > 0, "Staging sanciones vacio"
    assert Path("data/staging/osce_sanctions_registry.parquet").exists()
    assert Path("data/staging/osce_ruc_bridge.parquet").exists()
    log.log(f"  Sanciones staging: {len(s_df)} filas")
    log.log(f"  Bridge + penalidades + consorcios: OK")

def test_schemas(log):
    from backend.src.schemas.osce import OsceCompanyResponse
    from backend.src.schemas.candidates import CandidateResponse
    c = CandidateResponse(global_id="test")
    assert hasattr(c, "fup_url")
    assert hasattr(c, "ruc_sancionado")
    assert hasattr(c, "osce_match_method")
    assert hasattr(c, "osce_sancionada_match")
    log.log("  CandidateResponse: all OSCE fields present")
    o = OsceCompanyResponse(ruc="20100047218", fup_url="test")
    assert hasattr(o, "sanciones")
    log.log("  OsceCompanyResponse: schema OK")

if __name__ == "__main__":
    log = Logger(LOG_FILE)
    tests = [
        ("FUP URL builder", test_fup_url),
        ("Ingest sancionados", test_sancionados),
        ("Ingest penalidades", test_penalidades),
        ("Ingest consorcios", test_consorcios),
        ("Ingest conformacion juridica", test_conformacion),
        ("Build unified dataset", test_build_unified),
        ("Backend schemas", test_schemas),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        log.log(f"\n=== TEST: {name} ===")
        try:
            fn(log)
            log.log("  RESULT: PASS")
            passed += 1
        except Exception as e:
            log.log(f"  RESULT: FAIL - {e}")
            failed += 1
    log.log(f"\n{'='*40}")
    log.log(f"TOTAL: {passed} passed, {failed} failed")
    log.close()
    if failed > 0:
        sys.exit(1)
