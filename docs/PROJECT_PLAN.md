# Legal AI Agent — Project Plan

## Product Name: **LegalAI.in** (temporary)

## MVP Scope (8-10 weeks)

### Sprint 1: Foundation (Week 1-2)
- [x] Architecture design
- [x] Database schema design
- [ ] Supabase project setup + run migration
- [ ] FastAPI project scaffold
- [ ] Auth system (API key generation + validation)
- [ ] Basic project structure + CI/CD

### Sprint 2: Law Data Pipeline (Week 3-4)
- [ ] Crawl Indian Labour Law 2019 from indiankanoon.org
- [ ] Law parser — extract articles, clauses, points
- [ ] Chunking strategy implementation
- [ ] Embedding pipeline (BGE-M3 or OpenAI)
- [ ] Load into Supabase pgvector
- [ ] Crawl 5 key supporting Acts / Rules

### Sprint 3: RAG + Legal Q&A Agent (Week 5-6)
- [ ] Hybrid search implementation (semantic + keyword)
- [ ] Reranker integration
- [ ] Legal Q&A agent with Claude
- [ ] Citation verification system
- [ ] Hallucination guard
- [ ] API endpoint: POST /v1/legal/ask

### Sprint 4: Contract Review Agent (Week 7-8)
- [ ] Pydantic schema for Contract Review
- [ ] Extraction of entities (Parties, Clauses, Dates)
- [ ] Risk scoring logic based on templates
- [ ] NLP logic for compliance check
- [ ] API endpoint: POST /v1/contracts/review

### Sprint 5: Frontend & Polishing (Week 9-10)
- [ ] Simple Dashboard for API Key management
- [ ] Demo Chat UI for testing
- [ ] Rate limiting (Redis/Supabase)
- [ ] Billing logging structure
- [ ] MVP Launch

## Milestones

- **M1:** API auth and infrastructure ready.
- **M2:** Database populated with basic Indian Labour laws.
- **M3:** Legal Q&A agent answers basic legal queries with citations.
- **M4:** Contract Review agent correctly identifies risks in standard Employment Contracts.
- **M5:** MVP deployed and testable by early adopters.
