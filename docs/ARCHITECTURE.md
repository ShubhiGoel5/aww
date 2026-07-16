# Legal AI Agent — System Architecture

## Overview

A multi-tenant Legal AI platform for Indian companies. Companies interact via Cloud API to get AI-powered legal assistance — contract review, legal Q&A, compliance checking, and document drafting.

**Business Model:** SaaS API — companies authenticate with API keys, billed per usage tier.

---

## 1. System Architecture

```
                    ┌─────────────────────────┐
                    │      CLIENT APPS         │
                    │                          │
                    │  Web Dashboard (Next.js) │
                    │  Chat Widget (Embed JS)  │
                    │  REST API (Direct)       │
                    │  Mobile SDK (Future)     │
                    └───────────┬──────────────┘
                                │
                                │ HTTPS / WSS
                                ▼
┌───────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                       │
│                                                           │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │ Supabase    │  │ Rate     │  │ API Key  │  │Request│  │
│  │ Auth        │  │ Limiter  │  │ Validator│  │Logger │  │
│  │ (GoTrue)    │  │ (Redis)  │  │          │  │       │  │
│  └─────────────┘  └──────────┘  └──────────┘  └───────┘  │
│                                                           │
│  Supabase Edge Functions (auth, routing, billing meter)   │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATOR                       │
│                   (FastAPI + LangGraph)                     │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  Agent Router                        │  │
│  │  Analyzes intent → routes to specialized agent       │  │
│  └──────────┬──────────┬──────────┬──────────┬─────────┘  │
│             │          │          │          │             │
│     ┌───────▼──┐ ┌─────▼────┐ ┌──▼───────┐ ┌▼─────────┐  │
│     │ Legal    │ │ Contract │ │Compliance│ │ Document │  │
│     │ Q&A      │ │ Review   │ │ Audit    │ │ Drafter  │  │
│     │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │  │
│     └───────┬──┘ └────┬─────┘ └──┬───────┘ └┬─────────┘  │
│             │         │          │          │             │
│     ┌───────▼─────────▼──────────▼──────────▼─────────┐  │
│     │              Shared Services                     │  │
│     │                                                  │  │
│     │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│     │  │ Citation │ │ Halluc.  │ │ Context Manager  │  │  │
│     │  │ Verifier │ │ Guard    │ │ (Memory/History) │  │  │
│     │  └──────────┘ └──────────┘ └──────────────────┘  │  │
│     └──────────────────────────────────────────────────┘  │
└───────────────────────────┬───────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌──────────────────┐ ┌──────────┐ ┌──────────────────┐
│   RAG ENGINE     │ │   LLM    │ │   TOOL LAYER     │
│                  │ │  ROUTER  │ │                   │
│ Query Rewrite    │ │          │ │ OCR (Surya)       │
│ Hybrid Search    │ │ Claude   │ │ PDF Parser        │
│ Reranker         │ │ Sonnet   │ │ Doc Generator     │
│ Context Builder  │ │ (primary)│ │ Web Search        │
│                  │ │          │ │ Calculator        │
└────────┬─────────┘ └────┬─────┘ └──────────────────┘
         │                │
         └────────┬───────┘
                  ▼
┌───────────────────────────────────────────────────────────┐
│                     SUPABASE LAYER                         │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  PostgreSQL                          │  │
│  │                                                     │  │
│  │  ┌───────────┐  ┌───────────┐  ┌─────────────────┐  │  │
│  │  │ Tenant    │  │ Law DB    │  │ pgvector        │  │  │
│  │  │ Tables    │  │ (shared)  │  │ (embeddings)    │  │  │
│  │  │ (RLS)     │  │           │  │                 │  │  │
│  │  └───────────┘  └───────────┘  └─────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Auth    │  │ Storage  │  │ Realtime │  │  Edge    │  │
│  │ (GoTrue) │  │ (S3)     │  │ (WSS)    │  │Functions │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Data Architecture

### 2.1 Multi-Tenant Isolation

```
                    ┌──────────────────┐
                    │   Shared Layer    │
                    │                  │
                    │  law_documents   │  ← All VN laws
                    │  law_chunks      │  ← Embedded chunks
                    │  law_relations   │  ← Law cross-references
                    └──────────────────┘
                             │
                    READ-ONLY access via RLS
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Tenant A    │    │  Tenant B    │    │  Tenant C    │
│              │    │              │    │              │
│ company_id=A │    │ company_id=B │    │ company_id=C │
│              │    │              │    │              │
│ - documents  │    │ - documents  │    │ - documents  │
│ - chunks     │    │ - chunks     │    │ - chunks     │
│ - sessions   │    │ - sessions   │    │ - sessions   │
│ - messages   │    │ - messages   │    │ - messages   │
│ - usage_logs │    │ - usage_logs │    │ - usage_logs │
└──────────────┘    └──────────────┘    └──────────────┘

RLS Policy: WHERE company_id = auth.jwt()->>'company_id'
```

### 2.2 Law Data Pipeline

```
┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Source Sites   │     │  Crawler     │     │  Parser      │
│                 │     │              │     │              │
│ thuvienphapluat │────▶│ webcrawl.py  │────▶│ law_parser   │
│ luatindia     │     │ (scrape)     │     │ (extract     │
│ vanban.gov      │     │              │     │  articles)   │
└────────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                                                   ▼
┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Supabase      │     │  Embedder    │     │  Chunker     │
│  pgvector      │◀────│              │◀────│              │
│                │     │ BGE-M3 or    │     │ Split by     │
│ law_chunks +   │     │ OpenAI       │     │ article/     │
│ embedding      │     │              │     │ clause       │
└────────────────┘     └──────────────┘     └──────────────┘
```

### 2.3 Entity Relationship Diagram

```
companies ─────┬──── users
    │          │
    │          └──── api_keys
    │
    ├──── chat_sessions ──── messages
    │
    ├──── documents ──── company_chunks (pgvector)
    │
    └──── usage_logs

law_documents ──── law_chunks (pgvector)
       │
       └──── law_relations (cross-references)
```

---

## 3. Agent Architecture

### 3.1 Agent Router (Intent Classification)

```
User Input
    │
    ▼
┌───────────────────────────────┐
│  Intent Classifier (LLM)      │
│                               │
│  Classify into:               │
│  ├── LEGAL_QA                 │ → "Thai sn bao lu?"
│  ├── CONTRACT_REVIEW          │ → "Review hp ng ny"
│  ├── COMPLIANCE_CHECK         │ → "Cng ty ti c vi phm?"
│  ├── DOCUMENT_DRAFT           │ → "Son hp ng lao ng"
│  ├── CASE_RESEARCH            │ → "Tm n l tng t"
│  └── GENERAL_CHAT             │ → "Cho bn"
│                               │
│  Also extracts:               │
│  - Legal domain (labor, tax)  │
│  - Entities (company, person) │
│  - Urgency level              │
└───────────────┬───────────────┘
                │
                ▼
        Route to specialized agent
```

### 3.2 Legal Q&A Agent (Detail)

```
┌─────────────────────────────────────────────────────┐
│                LEGAL Q&A AGENT                       │
│                                                     │
│  Step 1: ANALYZE                                    │
│  ┌───────────────────────────────────┐              │
│  │ - Identify legal domain           │              │
│  │ - Extract key legal concepts      │              │
│  │ - Determine relevant laws         │              │
│  │ - Generate search queries (3-5)   │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 2: RETRIEVE                                   │
│  ┌───────────────────────────────────┐              │
│  │ Hybrid Search:                    │              │
│  │ ├── Semantic (pgvector cosine)    │              │
│  │ ├── Keyword (ts_vector BM25)      │              │
│  │ └── Filter (domain, status)       │              │
│  │                                   │              │
│  │ → Retrieve top 20 chunks          │              │
│  │ → Rerank to top 5                 │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 3: REASON                                     │
│  ┌───────────────────────────────────┐              │
│  │ LLM with retrieved context:       │              │
│  │ - Answer the legal question       │              │
│  │ - Cite specific articles          │              │
│  │ - Note any exceptions/conditions  │              │
│  │ - Flag if answer is uncertain     │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 4: VERIFY                                     │
│  ┌───────────────────────────────────┐              │
│  │ Citation Checker:                 │              │
│  │ - Verify each citation exists     │              │
│  │ - Confirm quote matches source    │              │
│  │ - Check law is still active       │              │
│  │ - Flag expired/amended laws       │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 5: FORMAT                                     │
│  ┌───────────────────────────────────┐              │
│  │ Response Builder:                 │              │
│  │ - Clear Indian answer         │              │
│  │ - Structured citations            │              │
│  │ - Confidence level                │              │
│  │ - Related topics suggestion       │              │
│  │ - Disclaimer                      │              │
│  └───────────────────────────────────┘              │
└─────────────────────────────────────────────────────┘
```

### 3.3 Contract Review Agent (Detail)

```
┌─────────────────────────────────────────────────────┐
│              CONTRACT REVIEW AGENT                   │
│                                                     │
│  Step 1: INGEST                                     │
│  ┌───────────────────────────────────┐              │
│  │ Upload → Supabase Storage         │              │
│  │ PDF/DOCX/Image → OCR if needed    │              │
│  │ → Extract full text               │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 2: CLASSIFY                                   │
│  ┌───────────────────────────────────┐              │
│  │ Contract Type Detection:          │              │
│  │ ├── Employment Contract            │              │
│  │ ├── Hp ng thng mi          │              │
│  │ ├── Hp ng thu/mua bn        │              │
│  │ ├── Service Contract             │              │
│  │ └── Hp ng hp tc             │              │
│  │                                   │              │
│  │ → Load relevant law checklist     │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 3: EXTRACT                                    │
│  ┌───────────────────────────────────┐              │
│  │ Key Clause Extraction:            │              │
│  │ - Parties (Bn A, Bn B)          │              │
│  │ - Term & Duration                 │              │
│  │ - Payment terms                   │              │
│  │ - Obligations & Rights            │              │
│  │ - Termination conditions          │              │
│  │ - Dispute resolution              │              │
│  │ - Penalties & Liabilities         │              │
│  │ - Confidentiality                 │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 4: ANALYZE                                    │
│  ┌───────────────────────────────────┐              │
│  │ Risk Assessment:                  │              │
│  │                                   │              │
│  │ For each clause:                  │              │
│  │ ├── Compare with VN law           │              │
│  │ ├── Check for missing clauses     │              │
│  │ ├── Identify unfair terms         │              │
│  │ ├── Flag legal violations         │              │
│  │ └── Score risk (LOW/MED/HIGH)     │              │
│  │                                   │              │
│  │ Missing Clause Check:             │              │
│  │ ├── Required by law but missing   │              │
│  │ ├── Best practice but missing     │              │
│  │ └── Recommended additions         │              │
│  └───────────────────┬───────────────┘              │
│                      ▼                              │
│  Step 5: REPORT                                     │
│  ┌───────────────────────────────────┐              │
│  │ Generate Review Report:           │              │
│  │                                   │              │
│  │ ┌─ Summary ──────────────────┐    │              │
│  │ │ Overall Risk: MEDIUM       │    │              │
│  │ │ Issues Found: 5            │    │              │
│  │ │ Critical: 1, Warning: 3   │    │              │
│  │ └───────────────────────────┘    │              │
│  │                                   │              │
│  │ ┌─ Issue Detail ─────────────┐    │              │
│  │ │ 🔴 Article 5: Vi phm iu   │    │              │
│  │ │    22 BLL — H xc regulation  │    │              │
│  │ │    time hn > 36 thng     │    │              │
│  │ │    →  xut: Sa thnh   │    │              │
│  │ │    "khng qu 36 thng"    │    │              │
│  │ └───────────────────────────┘    │              │
│  └───────────────────────────────────┘              │
└─────────────────────────────────────────────────────┘
```

---

## 4. RAG Engine (Deep Dive)

### 4.1 Embedding Strategy

```
Law Document
    │
    ▼
┌──────────────────────────────┐
│  Chunking Strategy            │
│                              │
│  Level 1: Per Article         │  "iu 41. n phng chm dt..."
│  Level 2: Per Clause          │  "Khon 1. Ngi s dng L..."
│  Level 3: Per Point           │  "im a) Khng b tr ng..."
│                              │
│  Each chunk includes:         │
│  - Content (text)            │
│  - Parent article context    │
│  - Law metadata              │
│  - Cross-references          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Embedding Models             │
│                              │
│  Primary: BGE-M3              │  Self-hosted, free
│  - Dense embedding (1024d)   │  Semantic similarity
│  - Sparse embedding          │  Keyword matching
│  - ColBERT embedding         │  Late interaction
│                              │
│  Backup: OpenAI ada-002      │  If BGE insufficient
│  - 1536 dimensions           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Storage: pgvector            │
│                              │
│  law_chunks table:            │
│  - id, law_id, article       │
│  - content (full text)       │
│  - embedding vector(1024)    │
│  - sparse_vector (tsvector)  │
│  - metadata (jsonb)          │
│                              │
│  Indexes:                    │
│  - HNSW for dense search     │
│  - GIN for sparse/keyword    │
│  - B-tree for metadata       │
└──────────────────────────────┘
```

### 4.2 Hybrid Search Pipeline

```sql
-- Dense search (semantic)
WITH semantic AS (
  SELECT id, content, metadata,
         1 - (embedding <=> query_embedding) AS semantic_score
  FROM law_chunks
  WHERE category && ARRAY['lao_dong']  -- metadata filter
  ORDER BY embedding <=> query_embedding
  LIMIT 20
),

-- Sparse search (keyword/BM25)
keyword AS (
  SELECT id, content, metadata,
         ts_rank_cd(search_vector, plainto_tsquery('indian', :query)) AS keyword_score
  FROM law_chunks
  WHERE search_vector @@ plainto_tsquery('indian', :query)
  ORDER BY keyword_score DESC
  LIMIT 20
),

-- Reciprocal Rank Fusion
combined AS (
  SELECT id, content, metadata,
         COALESCE(s.semantic_score, 0) * 0.7 +
         COALESCE(k.keyword_score, 0) * 0.3 AS combined_score
  FROM semantic s
  FULL OUTER JOIN keyword k USING (id, content, metadata)
  ORDER BY combined_score DESC
  LIMIT 10
)
SELECT * FROM combined;
```

### 4.3 Context Window Management

```
┌─────────────────────────────────────┐
│  Context Budget: 100K tokens         │
│                                     │
│  ┌─ System Prompt ──────── 2K ──┐   │
│  │ Legal AI personality & rules  │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ Conversation History ── 5K ──┐  │
│  │ Last 5-10 messages            │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ Retrieved Law Chunks ── 15K ─┐  │
│  │ Top 5-8 relevant chunks       │   │
│  │ With full article context     │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ Company Context ──── 5K ────┐   │
│  │ Company docs if relevant      │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ User Query ──────── 1K ─────┐   │
│  │ Current question              │   │
│  └──────────────────────────────┘   │
│                                     │
│  Reserved for response: ~70K        │
└─────────────────────────────────────┘
```

---

## 5. API Design

### 5.1 REST Endpoints

```
Authentication:
  POST   /v1/auth/register          # Company registration
  POST   /v1/auth/login              # User login
  POST   /v1/auth/api-keys           # Generate API key
  DELETE /v1/auth/api-keys/:id       # Revoke API key

Legal Q&A:
  POST   /v1/legal/ask               # Ask a legal question
  POST   /v1/legal/search            # Search law database
  GET    /v1/legal/laws/:id          # Get specific law document
  GET    /v1/legal/laws              # List/filter laws

Contract Review:
  POST   /v1/contracts/review        # Upload & review contract
  GET    /v1/contracts/:id/status    # Check review progress
  GET    /v1/contracts/:id/report   # Get review report

Compliance:
  POST   /v1/compliance/check        # Run compliance audit
  GET    /v1/compliance/checklists   # Get compliance checklists

Documents:
  POST   /v1/documents/draft         # Generate legal document
  GET    /v1/documents/templates     # List templates

Chat (Realtime):
  WS     /v1/chat                    # WebSocket chat session
  POST   /v1/chat/sessions           # Create chat session
  GET    /v1/chat/sessions/:id      # Get session history

Usage & Billing:
  GET    /v1/usage                   # Current period usage
  GET    /v1/usage/history           # Usage history
  GET    /v1/billing/invoices        # Invoices
```

### 5.2 Request/Response Examples

```json
// POST /v1/legal/ask
{
  "question": "Nhn vin ngh thai sn c bao lu?",
  "context": {
    "company_type": "manufacturing",
    "employee_count": 500
  },
  "options": {
    "include_citations": true,
    "include_related": true,
    "language": "vi"
  }
}

// Response
{
  "answer": "Theo rule regulation php lut n , lao ng n c ngh thai sn 06 thng...",
  "confidence": 0.95,
  "citations": [
    {
      "law": "Code Lao ng 2019",
      "number": "45/2019/QH14",
      "article": "iu 139",
      "clause": "Khon 1",
      "text": "Lao ng n c ngh thai sn trc v sau khi sinh con l 06 thng...",
      "effective_date": "2021-01-01",
      "status": "active"
    }
  ],
  "related_topics": [
    "Ch  BHXH thai sn",
    "Quyn li lao ng n mang thai",
    "Cm sa thi lao ng n mang thai"
  ],
  "disclaimer": "Ni dung t vn mang tnh tham kho. Vui lng tham kho  kin lut s cho trng hp c th.",
  "usage": {
    "tokens_used": 1847,
    "cost_usd": 0.0037
  }
}
```

```json
// POST /v1/contracts/review
// Content-Type: multipart/form-data
{
  "file": "<binary>",
  "contract_type": "labor",  // auto-detect if omitted
  "review_depth": "comprehensive",  // quick | standard | comprehensive
  "focus_areas": ["termination", "compensation", "compliance"]
}

// Response (async — returns job ID)
{
  "job_id": "rev_abc123",
  "status": "processing",
  "estimated_time": 30,  // seconds
  "webhook_url": "optional callback"
}

// GET /v1/contracts/rev_abc123/report
{
  "overall_risk": "MEDIUM",
  "score": 72,  // out of 100
  "summary": "Hp ng c 2 iu khon vi phm php lut v 3 iu khon bt li cho ngi lao ng.",
  "issues": [
    {
      "severity": "CRITICAL",
      "clause": "Article 5 - Thi hn hp ng",
      "issue": "Hp ng xc regulation time hn 48 thng, vt qu gii hn 36 thng",
      "law_reference": "iu 22, BLL 2019",
      "recommendation": "Sa time hn khng qu 36 thng, hoc chuyn thnh H khng xc regulation time hn"
    },
    {
      "severity": "WARNING",
      "clause": "iu 8 - Chm dt H",
      "issue": "Thiu rule regulation v time period bo trc khi n phng chm dt",
      "law_reference": "iu 36, Khon 1, BLL 2019",
      "recommendation": "B sung: NL bo trc 30-45 day ty loi H"
    }
  ],
  "missing_clauses": [
    "iu khon v BHXH, BHYT, BHTN",
    "Quy regulation v ngh php nm",
    "iu khon bo mt thng tin"
  ],
  "compliance_status": {
    "labor_code": "PARTIAL",
    "insurance": "MISSING",
    "safety": "OK"
  }
}
```

---

## 6. Security Architecture

### 6.1 Data Protection

```
┌─────────────────────────────────────────┐
│           Security Layers                │
│                                         │
│  Layer 1: Transport                     │
│  └── TLS 1.3 (all connections)          │
│                                         │
│  Layer 2: Authentication                │
│  └── Supabase Auth (JWT + API keys)     │
│  └── API key hashed with bcrypt         │
│  └── JWT expiry: 1 hour                 │
│                                         │
│  Layer 3: Authorization                 │
│  └── RLS policies on every table        │
│  └── Role-based (admin/member/viewer)   │
│  └── Resource-level permissions         │
│                                         │
│  Layer 4: Data Isolation                │
│  └── company_id on every row            │
│  └── RLS enforced at DB level           │
│  └── Storage buckets per company        │
│                                         │
│  Layer 5: Encryption                    │
│  └── At-rest: Supabase managed          │
│  └── Sensitive fields: pgcrypto         │
│  └── File storage: encrypted buckets    │
│                                         │
│  Layer 6: Audit                         │
│  └── Every API call logged              │
│  └── Every document access tracked      │
│  └── Retention: 90 days                 │
└─────────────────────────────────────────┘
```

### 6.2 LLM Safety

```
┌─────────────────────────────────────────┐
│         LLM Safety Guards                │
│                                         │
│  ① Input Sanitization                   │
│  └── Strip injection attempts           │
│  └── Validate document content          │
│  └── Block prompt injection             │
│                                         │
│  ② Output Validation                    │
│  └── Citation verification              │
│  └── Hallucination detection            │
│  └── Legal accuracy check               │
│  └── Confidence scoring                 │
│                                         │
│  ③ Guardrails                           │
│  └── Never give advice on criminal law  │
│  └── Always include disclaimer          │
│  └── Flag low-confidence answers        │
│  └── Refuse to impersonate lawyer       │
│                                         │
│  ④ Monitoring                           │
│  └── Log all LLM interactions           │
│  └── Alert on unusual patterns          │
│  └── Track accuracy metrics             │
└─────────────────────────────────────────┘
```

---

## 7. Deployment Architecture

### Phase 1: MVP (0-100 users)

```
┌──────────────────────────────────────┐
│          Supabase Cloud               │
│          (Free → Pro $25/mo)          │
│                                      │
│  Postgres + pgvector + Auth          │
│  + Storage + Realtime                │
└──────────────────┬───────────────────┘
                   │
┌──────────────────┴───────────────────┐
│     Single VPS (Hetzner CX31)        │
│     4 vCPU, 16GB RAM, $15/mo         │
│                                      │
│  Docker Compose:                     │
│  ├── fastapi-app (Agent server)      │
│  ├── redis (Queue + Cache)           │
│  ├── celery-worker (Async tasks)     │
│  └── caddy (Reverse proxy + SSL)     │
└──────────────────────────────────────┘
```

### Phase 2: Growth (100-1000 users)

```
┌──────────────────────────────────────┐
│          Supabase Pro ($25/mo)        │
│          + Dedicated DB ($100/mo)     │
└──────────────────┬───────────────────┘
                   │
┌──────────────────┴───────────────────┐
│     Kubernetes (2-3 nodes)            │
│     or Docker Swarm                   │
│                                      │
│  ├── api-server (2-3 replicas)       │
│  ├── celery-worker (2-4 replicas)    │
│  ├── redis-cluster                   │
│  ├── embedding-server (BGE-M3)       │
│  └── monitoring (Grafana + Loki)     │
└──────────────────────────────────────┘
```

### Phase 3: Scale (1000+ users)

```
┌──────────────────────────────────────┐
│     Supabase Enterprise               │
│     or Self-hosted Supabase           │
│     + Read replicas                   │
└──────────────────┬───────────────────┘
                   │
┌──────────────────┴───────────────────┐
│     Multi-region deployment           │
│     CDN + Load Balancer              │
│     Auto-scaling worker pools        │
│     Dedicated embedding GPU server   │
└──────────────────────────────────────┘
```

---

## 8. Indian Law Data Structure

### 8.1 Law Hierarchy

```
Hin php (Constitution)
    │
    ├── Code (Code)
    │   ├── Code Lao ng 2019
    │   ├── Code Dn s 2015
    │   └── Code Hnh s 2015
    │
    ├── Lut (Law)
    │   ├── Lut Doanh nghip 2020
    │   ├── Lut u t 2020
    │   └── Lut Thng mi 2005
    │
    ├── Decree (Decree) — Chnh ph
    │   ├── N 145/2020/N-CP (hng dn BLL)
    │   └── N 152/2020/N-CP (lao ng nc ngoi)
    │
    ├── Thng t (Circular) — B ngnh
    │   └── TT 09/2020/TT-BLTBXH
    │
    └── Vn bn khc
        ├── Quyt regulation
        ├── Ngh rulet
        └── Cng vn (reference only)
```

### 8.2 Priority Crawl List (MVP)

```
Phase 1 — Labor Law (HRVN use case):
  ├── Code Lao ng 2019 (45/2019/QH14)
  ├── N 145/2020/N-CP
  ├── N 135/2020/N-CP (tui ngh hu)
  ├── Lut BHXH 2024
  ├── Lut ATVSL 2015
  └── Cc thng t hng dn

Phase 2 — Business Law:
  ├── Lut Doanh nghip 2020
  ├── Lut u t 2020
  ├── Lut Thng mi 2005
  └── Lut Cnh tranh 2018

Phase 3 — Contract & Civil:
  ├── Code Dn s 2015
  ├── Lut Nh  2023
  ├── Lut Kinh doanh BS 2023
  └── Lut S hu tr tu 2005

Phase 4 — Tax & Finance:
  ├── Lut Thu TNCN
  ├── Lut Thu TNDN
  ├── Lut Thu GTGT
  └── Lut K ton 2015
```

---

## 9. Monitoring & Observability

```
┌─────────────────────────────────────────┐
│           Monitoring Stack               │
│                                         │
│  Metrics: Prometheus + Grafana          │
│  ├── API latency (p50, p95, p99)        │
│  ├── LLM response time                  │
│  ├── RAG retrieval quality              │
│  ├── Error rates                        │
│  └── Usage per tenant                   │
│                                         │
│  Logs: Loki + Grafana                   │
│  ├── All API requests                   │
│  ├── LLM prompts & responses            │
│  ├── Error traces                       │
│  └── Security events                    │
│                                         │
│  Alerts:                                │
│  ├── Error rate > 5%                    │
│  ├── LLM latency > 10s                 │
│  ├── Low RAG relevance score            │
│  ├── Quota exceeded                     │
│  └── Security anomalies                │
│                                         │
│  AI Quality:                            │
│  ├── Citation accuracy rate             │
│  ├── User satisfaction (thumbs)         │
│  ├── Hallucination detection rate       │
│  └── Answer completeness score          │
└─────────────────────────────────────────┘
```

---

## 10. Cost Analysis

### Per-Request Cost Breakdown

| Component | Cost/Request | Notes |
|---|---|---|
| Claude Sonnet (input) | $0.003 | ~1K input tokens avg |
| Claude Sonnet (output) | $0.005 | ~500 output tokens avg |
| Embedding | $0.0001 | OpenAI ada-002 |
| Supabase DB | $0.00001 | Negligible |
| Compute | $0.001 | VPS amortized |
| **Total** | **~$0.009** | **~220 VND/request** |

### Monthly Cost at Scale

| Users | Requests/mo | LLM Cost | Infra | Total | Revenue (3tr/user) |
|---|---|---|---|---|---|
| 10 | 5,000 | $45 | $40 | $85 | $1,200 |
| 50 | 25,000 | $225 | $65 | $290 | $6,000 |
| 100 | 50,000 | $450 | $100 | $550 | $12,000 |
| 500 | 250,000 | $2,250 | $300 | $2,550 | $60,000 |

**Margin: 75-95%** depending on scale.
