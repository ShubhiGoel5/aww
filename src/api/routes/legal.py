"""Legal Q&A endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from src.models.schemas import LegalQuestionRequest, LegalAnswerResponse, LawSearchRequest, LawSearchResponse

router = APIRouter()

@router.post("/ask", response_model=LegalAnswerResponse)
async def ask_legal_question(request: LegalQuestionRequest):
    """Ask a legal question and get an AI-powered answer with citations."""
    # TODO: implement with RAG + Claude
    raise HTTPException(status_code=501, detail="Coming soon")

@router.post("/search", response_model=LawSearchResponse)
async def search_laws(request: LawSearchRequest):
    """Search the Indian law database."""
    # TODO: implement hybrid search
    raise HTTPException(status_code=501, detail="Coming soon")
