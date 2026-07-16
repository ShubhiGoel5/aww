"""RAG search engine — hybrid semantic + keyword search over Indian law."""

from dataclasses import dataclass
from typing import Optional

from src.services.supabase_client import get_supabase


@dataclass
class SearchResult:
    """A single search result from law database."""
    chunk_id: str
    law_id: str
    law_title: str
    law_number: str
    article: Optional[str]
    clause: Optional[str]
    content: str
    parent_context: Optional[str]
    semantic_score: float
    keyword_score: float
    combined_score: float
    law_status: str


async def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    domains: Optional[list[str]] = None,
    limit: int = 10,
    semantic_weight: float = 0.7,
) -> list[SearchResult]:
    """
    Perform hybrid search combining semantic and keyword search.
    
    Uses the search_law_chunks Postgres function defined in Supabase.
    """
    supabase = get_supabase()
    
    result = supabase.rpc(
        "search_law_chunks",
        {
            "query_embedding": query_embedding,
            "query_text": query_text,
            "filter_domains": domains,
            "match_count": limit,
            "semantic_weight": semantic_weight,
        }
    ).execute()
    
    return [
        SearchResult(
            chunk_id=r["id"],
            law_id=r["law_id"],
            law_title=r["law_title"],
            law_number=r["law_number"],
            article=r.get("article"),
            clause=r.get("clause"),
            content=r["content"],
            parent_context=r.get("parent_context"),
            semantic_score=r["semantic_score"],
            keyword_score=r["keyword_score"],
            combined_score=r["combined_score"],
            law_status=r["law_status"],
        )
        for r in result.data
    ]


async def search_by_article(
    law_number: str,
    article: str,
) -> Optional[dict]:
    """Look up a specific article by law number and article reference."""
    supabase = get_supabase()
    
    result = supabase.table("law_chunks") \
        .select("*, law_documents(title, law_number, status)") \
        .eq("article", article) \
        .execute()
    
    # Filter by law_number in application code
    for r in result.data:
        if r.get("law_documents", {}).get("law_number") == law_number:
            return r
    
    return None
