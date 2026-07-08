"""
Legal Document Crawler — Powered by BeautifulSoup and requests
Crawl Indian legal websites and index documents automatically.
"""
import os
import re
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import urlparse, urljoin
import ipaddress
import requests
from bs4 import BeautifulSoup
import concurrent.futures

logger = logging.getLogger(__name__)

# Supported legal sources
LEGAL_SOURCES = {
    "indiankanoon": {
        "name": "Indian Kanoon",
        "base_url": "https://indiankanoon.org",
        "discover_urls": [
            "https://indiankanoon.org/browse/",
        ],
        "description": "Largest Indian legal document database"
    },
    "indiacode": {
        "name": "India Code",
        "base_url": "https://www.indiacode.nic.in",
        "discover_urls": [
            "https://www.indiacode.nic.in/handle/123456789/1362/browse?type=actno",
        ],
        "description": "Official government legal portal"
    },
    "legislative": {
        "name": "Legislative Department",
        "base_url": "https://legislative.gov.in",
        "discover_urls": [
            "https://legislative.gov.in/laws/acts-of-parliament",
        ],
        "description": "Legislative Department of India"
    }
}

class LegalCrawler:
    def __init__(self, db_connection=None):
        """Initialize crawler using requests and BeautifulSoup."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 LegalAI/1.0"
        })
        self.enabled = True
        self.db = db_connection
    
    def crawl_url(self, url: str) -> Dict:
        """Crawl a single legal document URL."""
        if not self.enabled:
            return {"success": False, "error": "Crawler is disabled"}
            
        if not self._is_legal_url(url):
            return {"success": False, "error": "Invalid or unsafe URL"}
            
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string.strip() if soup.title else ""
            
            # Remove scripts, styles, and head
            for element in soup(["script", "style", "nav", "footer", "header", "head"]):
                element.decompose()
                
            text = soup.get_text(separator='\n')
            
            # Clean up extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                "success": True,
                "content": content,
                "title": title,
                "url": url,
                "content_type": "text/plain",
                "chars": len(content),
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP error occurred: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Crawl failed: {e}"}
    
    def discover_links(self, url: str, max_links: int = 50) -> List[str]:
        """Discover legal document links from a page."""
        if not self.enabled:
            return []
            
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(url, href)
                links.append(absolute_url)
                
            # Filter for legal document URLs and remove duplicates
            legal_links = list(dict.fromkeys([l for l in links if self._is_legal_url(l)]))
            return legal_links[:max_links]
        except Exception as e:
            logger.error(f"Discover failed: {e}")
            return []
    
    def crawl_and_index(self, url: str, company_id: str = None) -> Dict:
        """Crawl a URL and index it into the database."""
        # Step 1: Crawl
        result = self.crawl_url(url)
        if not result["success"]:
            return result
        
        content = result["content"]
        title = result["title"] or self._extract_title(content)
        
        if len(content) < 100:
            return {"success": False, "error": "Content too short to index"}
        
        # Step 2: Chunk content
        chunks = self._chunk_content(content, max_chunk_size=1000)
        
        # Step 3: Create document hash (dedup)
        content_hash = hashlib.md5(content[:5000].encode()).hexdigest()
        
        return {
            "success": True,
            "title": title,
            "url": url,
            "content_length": len(content),
            "chunks": len(chunks),
            "content_hash": content_hash,
            "document": {
                "title": title,
                "content": content,
                "url": url,
                "source": self._detect_source(url),
                "chunks": chunks,
            }
        }
    
    def batch_crawl(self, urls: List[str], company_id: str = None) -> Dict:
        """Crawl multiple URLs concurrently."""
        if not self.enabled:
            return {"success": False, "error": "Crawler is disabled"}
            
        indexed = 0
        errors = 0
        formatted_results = []
        
        def crawl_worker(url):
            return self.crawl_url(url)
            
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(crawl_worker, url): url for url in urls}
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        if result["success"] and len(result.get("content", "")) > 0:
                            indexed += 1
                            formatted_results.append({
                                "url": url,
                                "title": result.get("title", ""),
                                "content_length": len(result["content"])
                            })
                        else:
                            errors += 1
                    except Exception:
                        errors += 1
            
            return {
                "success": True,
                "total": len(urls),
                "indexed": indexed,
                "errors": errors,
                "results": formatted_results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_sources(self) -> List[Dict]:
        """Get list of supported legal sources."""
        return [
            {"id": k, **v} for k, v in LEGAL_SOURCES.items()
        ]
    
    def _is_legal_url(self, url: str) -> bool:
        """Check if URL is likely a legal document and safe."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Basic SSRF prevention
            hostname = parsed.hostname or ""
            if hostname in ('localhost', '127.0.0.1', '::1') or hostname.endswith('.local'):
                return False
                
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback:
                    return False
            except ValueError:
                pass # not an IP
        except Exception:
            return False

        legal_patterns = [
            r'act', r'ordinance', r'bill', r'rule',
            r'gazette', r'notification', r'code', r'law',
            r'statute', r'amendment', r'section', r'article',
            r'doc', r'judgment', r'order'
        ]
        url_lower = url.lower()
        return any(p in url_lower for p in legal_patterns)
    
    def _extract_title(self, content: str) -> str:
        """Extract title from content."""
        lines = content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        return "Untitled Document"
    
    def _chunk_content(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """Split content into chunks."""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _detect_source(self, url: str) -> str:
        """Detect source from URL."""
        for source_id, source in LEGAL_SOURCES.items():
            if source["base_url"] in url:
                return source["name"]
        return "Custom Source"
