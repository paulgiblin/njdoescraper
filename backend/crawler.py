import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

class ElectionCrawler:
    def __init__(self, start_url="https://www.nj.gov/state/elections/election-information-results.shtml", rate_limit=1):
        self.start_url = start_url
        self.rate_limit = rate_limit
        self.visited_urls = set()
        self.pdf_urls = set()
        self.running = False
        self.paused = False
        self.stats = {
            "pages_crawled": 0,
            "pdfs_found": 0,
            "pdfs_downloaded": 0,
            "current_url": "",
            "status": "stopped"
        }
        
        # Setup logging
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Setup PDF storage
        self.pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdfs')
        os.makedirs(self.pdf_dir, exist_ok=True)

    async def download_pdf(self, url, session):
        try:
            # Create year directory if it's a year-specific PDF
            year_match = re.search(r'(\d{4})', url)
            if year_match:
                year = year_match.group(1)
                year_dir = os.path.join(self.pdf_dir, year)
                os.makedirs(year_dir, exist_ok=True)
            else:
                year_dir = self.pdf_dir

            # Extract filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'

            filepath = os.path.join(year_dir, filename)

            # Skip if already downloaded
            if os.path.exists(filepath):
                self.logger.info(f"Skipping existing PDF: {filepath}")
                # Still count it in stats since we found it
                self.stats["pdfs_found"] += 1
                return

            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    self.stats["pdfs_downloaded"] += 1
                    self.stats["pdfs_found"] += 1
                    self.logger.info(f"Successfully downloaded PDF: {filepath}")
                else:
                    self.logger.error(f"Failed to download PDF {url}: Status {response.status}")
        except Exception as e:
            self.logger.error(f"Error downloading PDF {url}: {str(e)}")

    async def fetch_page(self, url, session):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.error(f"Error fetching {url}: Status {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Exception while fetching {url}: {str(e)}")
            return None

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        # Find the table containing election results
        results_table = soup.find('table', {'class': 'table table-hover'})
        if results_table:
            for a in results_table.find_all('a'):
                href = a.get('href')
                if href:
                    # Convert relative URLs to absolute URLs
                    full_url = urljoin(base_url, href)
                    
                    if href.endswith('.pdf'):
                        # Direct PDF link
                        self.pdf_urls.add(full_url)
                        self.stats["pdfs_found"] += 1
                        self.logger.info(f"Found PDF: {full_url}")
                    elif href.endswith('.shtml'):
                        # Election year page
                        links.add(full_url)
                        
        return links

    async def crawl_url(self, url, session):
        if url in self.visited_urls or not self.running or self.paused:
            return

        self.visited_urls.add(url)
        self.stats["current_url"] = url
        self.stats["pages_crawled"] += 1
        
        self.logger.info(f"Crawling: {url}")
        
        html = await self.fetch_page(url, session)
        if html:
            links = self.extract_links(html, url)
            
            # Download any PDFs found on this page
            pdf_tasks = []
            for pdf_url in self.pdf_urls - set(p for p, _ in pdf_tasks):
                if self.running and not self.paused:
                    await asyncio.sleep(self.rate_limit)
                    pdf_tasks.append(asyncio.create_task(self.download_pdf(pdf_url, session)))
            
            # Process each link
            for link in links:
                if self.running and not self.paused and link not in self.visited_urls:
                    await asyncio.sleep(self.rate_limit)  # Rate limiting
                    await self.crawl_url(link, session)
            
            # Wait for PDF downloads to complete
            if pdf_tasks:
                await asyncio.gather(*pdf_tasks)

    async def start(self):
        if not self.running:
            self.running = True
            self.stats["status"] = "running"
            self.logger.info("Crawler started")
            
            async with aiohttp.ClientSession() as session:
                await self.crawl_url(self.start_url, session)
            
            self.running = False
            self.stats["status"] = "stopped"
            self.logger.info("Crawler finished")

    def stop(self):
        self.running = False
        self.stats["status"] = "stopped"
        self.logger.info("Crawler stopped")

    def pause(self):
        self.paused = True
        self.stats["status"] = "paused"
        self.logger.info("Crawler paused")

    def resume(self):
        self.paused = False
        if self.running:
            self.stats["status"] = "running"
        self.logger.info("Crawler resumed")

    def set_rate_limit(self, rate_limit):
        self.rate_limit = rate_limit
        self.logger.info(f"Rate limit set to {rate_limit} seconds")

    def get_stats(self):
        return self.stats

    def get_results(self):
        return {
            "visited_urls": list(self.visited_urls),
            "pdf_urls": list(self.pdf_urls)
        }

# Create crawler instance
crawler = ElectionCrawler()
