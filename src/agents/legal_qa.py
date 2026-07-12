"""Legal Q&A Agent — answers legal questions using RAG over Indian law."""

import os
from typing import Optional

from src.rag.search import hybrid_search, SearchResult
from src.rag.embedder import get_embedder
from src.models.schemas import (
    LegalQuestionRequest,
    LegalAnswerResponse,
    Citation,
    LegalDomain,
)
from src.services.llm_provider import GroqProvider

SYSTEM_PROMPT = """You are a professional AI Legal Assistant specializing in Indian Law.

CAPABILITIES:
1. ANSWER legal questions — explain laws, lookup sections
2. DRAFT documents — contracts, applications, minutes, decisions, rules
3. ADVISE — analyze legal risks, propose solutions
4. REVIEW — check the legality of documents

When answering questions:
- Cite specific legal provisions (act name, section, subsection, clause)
- Use clear, easy-to-understand language for non-experts
- Prioritize currently valid legal texts

When drafting documents:
- Draft COMPLETELY, professionally, following Indian legal standards
- Mark places to fill: [INFORMATION TO FILL]
- Include all mandatory clauses according to law
- Clear formatting: clear headings, numbered clauses, signature section

Rules:
- Use the provided legal sources as the main reference
- Combine with general knowledge of Indian law to answer comprehensively
- DO NOT invent document numbers or specific sections
- If the source is insufficient, still support but note it clearly
- Always include a disclaimer: reference advice only, need an advocate for specific cases

Answer in English."""

DISCLAIMER = "This advice is for reference purposes only. Please consult an advocate for specific legal issues."


class LegalQAAgent:
    """Agent that answers legal questions using RAG."""
    
    def __init__(self):
        self.provider = GroqProvider()
        self.embedder = get_embedder()
    
    async def answer(self, request: LegalQuestionRequest) -> LegalAnswerResponse:
        """Process a legal question and return an answer with citations."""
        
        # Step 1: Embed the question
        query_embedding = await self.embedder.embed(request.question)
        
        # Step 2: Search for relevant law chunks
        domains = [d.value for d in request.domains] if request.domains else None
        search_results = await hybrid_search(
            query_embedding=query_embedding,
            query_text=request.question,
            domains=domains,
            limit=8,
        )
        
        # Step 3: Build context from search results
        context = self._build_context(search_results)
        
        # Step 4: Generate answer with Ollama
        answer_text, citations = await self._generate_answer(
            question=request.question,
            context=context,
            search_results=search_results,
        )
        
        # Step 5: Extract related topics
        related = self._extract_related_topics(search_results)
        
        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(search_results)
        
        return LegalAnswerResponse(
            answer=answer_text,
            confidence=confidence,
            citations=citations,
            related_topics=related,
            disclaimer=DISCLAIMER,
            usage={},  # TODO: track tokens
        )
    
    def _build_context(self, results: list[SearchResult]) -> str:
        """Build context string from search results."""
        parts = []
        for i, r in enumerate(results, 1):
            ref = f"[{i}] {r.law_title} ({r.law_number})"
            if r.article:
                ref += f" - {r.article}"
            if r.clause:
                ref += f", {r.clause}"
            ref += f" [Status: {r.law_status}]"
            
            parts.append(f"{ref}\n{r.content}")
        
        return "\n\n---\n\n".join(parts)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
        search_results: list[SearchResult],
    ) -> tuple[str, list[Citation]]:
        """Generate answer using Ollama with retrieved context."""
        
        user_prompt = f"""Based on the following legal sources, answer the question.

## Legal Sources:

{context}

## Question:

{question}

## Requirements:
- Answer clearly and structurally
- Cite specific sections/clauses from the source
- Note if the law is expired or amended
- Suggest related issues if necessary"""

        # Call Ollama Provider
        response = await self.provider.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=SYSTEM_PROMPT,
            max_tokens=2000
        )
        
        answer_text = response["content"][0]["text"]
        
        # Extract citations from search results used
        citations = []
        for r in search_results[:5]:  # Top 5 most relevant
            citations.append(Citation(
                law_title=r.law_title,
                law_number=r.law_number,
                article=r.article,
                clause=r.clause,
                text=r.content[:200] + "..." if len(r.content) > 200 else r.content,
                status=r.law_status,
            ))
        
        return answer_text, citations
    
    def _extract_related_topics(self, results: list[SearchResult]) -> list[str]:
        """Extract related topic suggestions from search results."""
        topics = set()
        for r in results:
            if r.article:
                topics.add(f"{r.law_title} - {r.article}")
        return list(topics)[:5]
    
    def _calculate_confidence(self, results: list[SearchResult]) -> float:
        """Calculate confidence score based on search quality."""
        if not results:
            return 0.0
        
        # Based on top result relevance
        top_score = results[0].combined_score
        
        # Adjust based on number of relevant results
        relevant_count = sum(1 for r in results if r.combined_score > 0.5)
        coverage_bonus = min(relevant_count * 0.05, 0.2)
        
        confidence = min(top_score + coverage_bonus, 1.0)
        return round(confidence, 2)
