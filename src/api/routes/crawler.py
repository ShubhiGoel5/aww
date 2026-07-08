"""
Crawler routes — Legal document crawling.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/crawler", tags=["crawler"])

class CrawlRequest(BaseModel):
    url: str

class BatchCrawlRequest(BaseModel):
    urls: List[str]

class DiscoverRequest(BaseModel):
    url: str
    max_links: int = 50

# Import auth from middleware
from ..middleware.auth import get_current_user, get_db

@router.get("/sources")
async def list_sources():
    """List supported legal document sources."""
    from ...services.crawler import LEGAL_SOURCES
    return {
        "sources": [{"id": k, **v} for k, v in LEGAL_SOURCES.items()],
        "powered_by": "Custom LegalCrawler"
    }

@router.post("/crawl")
async def crawl_document(req: CrawlRequest, user = Depends(get_current_user)):
    """Crawl a single legal document URL."""
    from ...services.crawler import LegalCrawler
    
    crawler = LegalCrawler()
    result = crawler.crawl_and_index(req.url)
    
    if not result["success"]:
        raise HTTPException(400, result["error"])
    
    return {
        **result,
        "powered_by": "Custom LegalCrawler"
    }

@router.post("/discover")
async def discover_links(req: DiscoverRequest, user = Depends(get_current_user)):
    """Discover legal document links from a page."""
    from ...services.crawler import LegalCrawler
    
    crawler = LegalCrawler()
    links = crawler.discover_links(req.url, req.max_links)
    
    return {
        "url": req.url,
        "links": links,
        "count": len(links),
        "powered_by": "Custom LegalCrawler"
    }

@router.post("/batch")
async def batch_crawl(req: BatchCrawlRequest, user = Depends(get_current_user)):
    """Batch crawl multiple URLs."""
    from ...services.crawler import LegalCrawler
    
    crawler = LegalCrawler()
    result = crawler.batch_crawl(req.urls)
    
    if not result["success"]:
        raise HTTPException(400, result["error"])
    
    return {
        **result,
        "powered_by": "Custom LegalCrawler"
    }

@router.get("/status")
async def crawler_status():
    """Check crawler status."""
    return {
        "configured": True,
        "message": "LegalCrawler is ready ✅"
    }
