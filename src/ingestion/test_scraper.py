import asyncio
from src.ingestion.deputy_scraper import DeputyScraper
from src.ingestion.senator_scraper import SenatorScraper


async def main():
    scraper = DeputyScraper()
    await scraper.run()
    scraper2 = SenatorScraper()
    await scraper2.run()

if __name__ == "__main__":
    asyncio.run(main())