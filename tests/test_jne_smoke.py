import sys
import asyncio
import os
from pathlib import Path

sys.path.append(os.getcwd())
LOG_FILE = "test_jne_results.log"

class Logger:
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
    def log(self, msg):
        self.f.write(msg + "\n")
        self.f.flush()
        print(msg)
    def close(self):
        self.f.close()

async def test_presidential_list(log):
    from src.ingestion.presidential_scraper import PresidentialScraper
    scraper = PresidentialScraper()
    log.log(f"  Testing URL: {scraper.list_url}")
    candidates = await scraper.get_candidate_list()
    assert len(candidates) > 0, "No se obtuvieron candidatos presidenciales"
    log.log(f"  Presidential list: {len(candidates)} candidates found (SUCCESS)")
    return candidates[0]

async def test_candidate_detail(log, id_hv):
    from src.ingestion.presidential_scraper import PresidentialScraper
    scraper = PresidentialScraper()
    log.log(f"  Testing Detail URL for IdHojaVida={id_hv}")
    sem = asyncio.Semaphore(1)
    # Using a fake output dir for smoke test
    scraper.output_dir = Path("data/raw/smoke_test")
    scraper.output_dir.mkdir(parents=True, exist_ok=True)
    success = await scraper.download_candidate_data(id_hv, sem)
    assert success, f"Fallo al descargar detalle para {id_hv}"
    log.log(f"  Candidate detail: SUCCESS")
    
    # Cleanup
    if (scraper.output_dir / f"{id_hv}.json").exists():
        (scraper.output_dir / f"{id_hv}.json").unlink()

async def test_parliament_list(log):
    from src.ingestion.parliament_scraper import ParliamentScraper
    scraper = ParliamentScraper()
    candidates = await scraper.get_candidate_list()
    assert len(candidates) > 0, "No se obtuvieron candidatos al parlamento"
    log.log(f"  Parliament list: {len(candidates)} candidates found (SUCCESS)")

async def main():
    log = Logger(LOG_FILE)
    log.log("=== JNE SMOKE TESTS ===")
    
    try:
        log.log("\n--- Presidential Scraper ---")
        first_candidate = await test_presidential_list(log)
        
        if first_candidate:
            await test_candidate_detail(log, first_candidate["idHojaVida"])
            
        log.log("\n--- Parliament Scraper ---")
        await test_parliament_list(log)
        
        log.log("\nTOTAL: ALL PASS")
    except Exception as e:
        log.log(f"\nFAILED: {e}")
        import traceback
        log.log(traceback.format_exc())
        sys.exit(1)
    finally:
        log.close()

if __name__ == "__main__":
    asyncio.run(main())