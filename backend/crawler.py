import asyncio
import logging
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime
from typing import Dict, Set, List
from pydantic import BaseModel
import json

class CrawlerStats(BaseModel):
    pages_crawled: int = 0
    pages_queued: int = 0
    start_time: str = None
    current_url: str = None
    errors: List[str] = []

class WebCrawler:
    def __init__(self):
        self.base_url = "https://www.nj.gov/state/elections/election-information-results.shtml"
        self.start_xpath = "/html/body/div[8]/div/div/div[1]/div/div/table"
        self.visited_urls: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.is_paused = False
        self.rate_limit = 1.0  # Default 1 second between requests
        self.stats = CrawlerStats()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/logs/crawler.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def start(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.stats.start_time = datetime.now().isoformat()
            await self.queue.put(self.base_url)
            await self.crawl()

    async def stop(self):
        self.is_running = False
        self.is_paused = False

    async def pause(self):
        self.is_paused = not self.is_paused

    def set_rate_limit(self, rate: float):
        self.rate_limit = max(0.1, rate)  # Minimum 100ms between requests

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue

                if self.queue.empty():
                    self.logger.info("Queue empty, crawling complete")
                    break

                url = await self.queue.get()
                if url in self.visited_urls:
                    continue

                try:
                    self.stats.current_url = url
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'lxml')
                            
                            # Find the starting table using XPath-like navigation
                            table = soup.select_one("div.container table")
                            if table:
                                links = table.find_all('a')
                                for link in links:
                                    href = link.get('href')
                                    if href:
                                        if not href.startswith('http'):
                                            href = f"https://www.nj.gov{href}"
                                        if href not in self.visited_urls:
                                            await self.queue.put(href)
                                            self.stats.pages_queued += 1

                            self.visited_urls.add(url)
                            self.stats.pages_crawled += 1
                            self.logger.info(f"Crawled: {url}")
                        else:
                            self.logger.error(f"Error {response.status} for URL: {url}")
                            self.stats.errors.append(f"HTTP {response.status} - {url}")

                except Exception as e:
                    self.logger.error(f"Error crawling {url}: {str(e)}")
                    self.stats.errors.append(f"Error: {str(e)} - {url}")

                await asyncio.sleep(self.rate_limit)

    def get_stats(self) -> Dict:
        return self.stats.dict()

# Create crawler instance
crawler = WebCrawler()
