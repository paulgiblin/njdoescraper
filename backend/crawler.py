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
        self.reset_state()
        
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

    def reset_state(self):
        """Reset all crawler state variables to their initial values."""
        self.running = False
        self.visited_urls = set()
        self.pdf_urls = set()
        self.link_tree = {
            "nodes": [{
                "id": self.start_url,
                "type": "page",
                "name": "Start Page",
                "status": "pending"
            }],
            "links": []
        }
        self.pdf_states = {}  # Tracks states: "queued", "downloaded", "failed"
        self.stats = {
            "pages_crawled": 0,
            "pdfs_found": 0,
            "pdfs_downloaded": 0,
            "current_url": "",
            "status": "stopped",
            "link_tree": self.link_tree
        }

    async def download_pdf(self, url, session):
        try:
            # Extract year from URL
            year_match = re.search(r'(\d{4})', url)
            if not year_match:
                self.logger.warning(f"Could not extract year from URL: {url}")
                self.pdf_states[url] = "failed"
                return

            year = year_match.group(1)
            year_dir = os.path.join(self.pdf_dir, year)
            os.makedirs(year_dir, exist_ok=True)

            # Extract filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'

            filepath = os.path.join(year_dir, filename)

            # Skip if already downloaded
            if os.path.exists(filepath):
                self.pdf_states[url] = "downloaded"
                return

            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    self.stats["pdfs_downloaded"] += 1
                    self.pdf_states[url] = "downloaded"
                    self.logger.info(f"Successfully downloaded PDF: {filepath}")
                else:
                    self.pdf_states[url] = "failed"
                    self.logger.error(f"Failed to download PDF {url}: Status {response.status}")
        except Exception as e:
            self.pdf_states[url] = "failed"
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
                    
                    # Skip if we've already seen this URL
                    if full_url in self.visited_urls:
                        continue
                    
                    # Add node to link tree if not exists
                    if not any(node["id"] == full_url for node in self.link_tree["nodes"]):
                        node_type = "pdf" if href.endswith('.pdf') else "page"
                        self.link_tree["nodes"].append({
                            "id": full_url,
                            "type": node_type,
                            "name": os.path.basename(urlparse(full_url).path)
                        })
                        # Add link from current page to this node
                        self.link_tree["links"].append({
                            "source": base_url,
                            "target": full_url
                        })
                    
                    if href.endswith('.pdf'):
                        if any(term in href.lower() for term in ['-general-election', '-primary-election']):
                            if full_url not in self.pdf_urls:
                                self.pdf_urls.add(full_url)
                                self.pdf_states[full_url] = "queued"
                                self.stats["pdfs_found"] += 1
                                self.logger.info(f"Found election PDF: {full_url}")
                    elif href.endswith('.shtml'):
                        if 'election' in href.lower():
                            links.add(full_url)
                            self.logger.info(f"Found election page: {full_url}")
        
        return links

    async def crawl_url(self, url, session):
        if url in self.visited_urls or not self.running:
            return

        # Mark as visited before processing to prevent duplicate processing
        self.visited_urls.add(url)
        self.stats["current_url"] = url
        self.stats["pages_crawled"] += 1
        
        # Update node status in link tree
        for node in self.link_tree["nodes"]:
            if node["id"] == url:
                node["status"] = "visited"
                break
        else:
            # Add the current URL to the link tree if not exists
            node = {
                "id": url,
                "type": "page",
                "name": os.path.basename(urlparse(url).path) or "Home",
                "status": "visited"
            }
            self.link_tree["nodes"].append(node)
        
        # Make a deep copy of link_tree to ensure it's properly updated in stats
        self.stats["link_tree"] = {
            "nodes": self.link_tree["nodes"].copy(),
            "links": self.link_tree["links"].copy()
        }
        
        self.logger.info(f"Crawling: {url}")
        
        html = await self.fetch_page(url, session)
        if html:
            links = self.extract_links(html, url)
            
            # Process PDFs found on this page
            new_pdfs = self.pdf_urls - set(self.visited_urls)
            for pdf_url in new_pdfs:
                if self.running:
                    # Add PDF to link tree
                    if not any(node["id"] == pdf_url for node in self.link_tree["nodes"]):
                        node = {
                            "id": pdf_url,
                            "type": "pdf",
                            "name": os.path.basename(urlparse(pdf_url).path),
                            "status": "queued"
                        }
                        self.link_tree["nodes"].append(node)
                        self.link_tree["links"].append({
                            "source": url,
                            "target": pdf_url
                        })
                        # Update stats with a deep copy of the new link_tree
                        self.stats["link_tree"] = {
                            "nodes": self.link_tree["nodes"].copy(),
                            "links": self.link_tree["links"].copy()
                        }
                    
                    await asyncio.sleep(self.rate_limit)
                    await self.download_pdf(pdf_url, session)
                    
                    # Update PDF node status after download
                    for node in self.link_tree["nodes"]:
                        if node["id"] == pdf_url:
                            node["status"] = self.pdf_states.get(pdf_url, "failed")
                            break
                    
                    # Update stats with the latest link_tree
                    self.stats["link_tree"] = {
                        "nodes": self.link_tree["nodes"].copy(),
                        "links": self.link_tree["links"].copy()
                    }
            
            # Process each new link
            for link in links:
                if (self.running and 
                    link not in self.visited_urls and 
                    not link.endswith('.pdf')):
                    # Add link to link tree
                    if not any(node["id"] == link for node in self.link_tree["nodes"]):
                        self.link_tree["links"].append({
                            "source": url,
                            "target": link
                        })
                        # Update stats with the new link_tree
                        self.stats["link_tree"] = {
                            "nodes": self.link_tree["nodes"].copy(),
                            "links": self.link_tree["links"].copy()
                        }
                    
                    await asyncio.sleep(self.rate_limit)
                    await self.crawl_url(link, session)

    async def start(self):
        """Start the crawler with a fresh state."""
        if not self.running:
            self.reset_state()  # Reset state before starting
            self.running = True
            self.stats["status"] = "running"
            self.logger.info("Starting crawler")
            try:
                async with aiohttp.ClientSession() as session:
                    await self.crawl_url(self.start_url, session)
            except Exception as e:
                self.logger.error(f"Error in crawler: {str(e)}")
            finally:
                if self.running:  
                    self.running = False
                    self.stats["status"] = "stopped"
                    self.logger.info("Crawling completed")

    def stop(self):
        self.running = False
        self.stats["status"] = "stopped"
        self.logger.info("Crawler stopped by user")

    def set_rate_limit(self, rate_limit):
        self.rate_limit = rate_limit
        self.logger.info(f"Rate limit set to {rate_limit} seconds")

    def get_stats(self):
        return self.stats

    def get_results(self):
        return {
            "visited_urls": list(self.visited_urls),
            "pdf_urls": list(self.pdf_urls),
            "link_tree": self.link_tree,
            "pdf_states": self.pdf_states
        }

# Create crawler instance
crawler = ElectionCrawler()
