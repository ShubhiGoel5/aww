# Database Schema — Supabase

## Setup Instructions

1. Create Supabase project at https://supabase.com
2. Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Run the migration below

## Full Migration

```sql
-- ============================================
-- LEGAL AI AGENT — SUPABASE DATABASE SCHEMA
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;        -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- encryption
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- trigram for fuzzy search

-- ============================================
-- 1. TENANT MANAGEMENT
-- ============================================

CREATE TYPE plan_type AS ENUM ('trial', 'starter', 'pro', 'enterprise');
CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member', 'viewer');

CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,  -- URL-friendly identifier
  plan plan_type DEFAULT 'trial',
  
  -- Quotas
  monthly_quota INT DEFAULT 50,  -- trial = 50 free requests
  used_quota INT DEFAULT 0,
  quota_reset_at TIMESTAMPTZ DEFAULT (date_trunc('month', now()) + interval '1 month'),
  
  -- Settings
  settings JSONB DEFAULT '{
    "default_language": "vi",
    "notification_email": null,
    "webhook_url": null,
    "allowed_domains": [],
    "custom_disclaimer": null
  }',
  
  -- Metadata
  industry TEXT,  -- manufacturing, retail, tech, etc.
  employee_count INT,
  tax_code TEXT,  -- M number thu
  
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name TEXT NOT NULL,  -- "Production", "Testing"
  key_hash TEXT NOT NULL,  -- bcrypt hash of actual key
  key_prefix TEXT NOT NULL,  -- "lak_abc..." (first 8 chars for identification)
  permissions TEXT[] DEFAULT ARRAY['read', 'ask', 'review'],
  rate_limit INT DEFAULT 60,  -- requests per minute
  is_active BOOLEAN DEFAULT true,
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
  role user_role DEFAULT 'member',
  full_name TEXT,
  email TEXT,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_api_keys_company ON api_keys(company_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);

-- ============================================
-- 2. INDIAN LAW DATABASE (SHARED)
-- ============================================

CREATE TYPE law_type AS ENUM (
  'hien_phap',    -- Constitution
  'bo_luat',      -- Code (Code)
  'luat',         -- Law (Lut)
  'nghi_dinh',    -- Decree (Decree)
  'thong_tu',     -- Circular (Circular)
  'ruleet_dinh',   -- Decision (Decision)
  'nghi_ruleet',   -- Resolution (Ngh rulet)
  'cong_van',     -- Official dispatch
  'other'
);

CREATE TYPE law_status AS ENUM ('active', 'expired', 'amended', 'repealed', 'pending');
CREATE TYPE legal_domain AS ENUM (
  'lao_dong',     -- Labor
  'doanh_nghiep', -- Enterprise
  'dan_su',       -- Civil
  'thuong_mai',   -- Commercial
  'thue',         -- Tax
  'dat_dai',      -- Land
  'dau_tu',       -- Investment
  'bhxh',         -- Social insurance
  'atvs_ld',      -- Occupational safety
  'so_huu_tri_tue', -- Intellectual property
  'hinh_su',      -- Criminal (reference only)
  'other'
);

CREATE TABLE law_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identification
  title TEXT NOT NULL,
  law_number TEXT NOT NULL,  -- "45/2019/QH14"
  law_type law_type NOT NULL,
  
  -- Authority
  issuer TEXT NOT NULL,  -- "Quc hi", "Chnh ph", "B LTBXH"
  signer TEXT,  -- Person who signed
  
  -- Dates
  issued_date DATE,
  effective_date DATE,
  expiry_date DATE,
  
  -- Status & Relations
  status law_status DEFAULT 'active',
  domains legal_domain[] NOT NULL,
  replaces UUID[],  -- IDs of laws this replaces
  amended_by UUID[], -- IDs of laws that amend this
  
  -- Content
  full_text TEXT,
  summary TEXT,  -- AI-generated summary
  table_of_contents JSONB,  -- Structured TOC
  
  -- Source
  source_url TEXT,
  source_site TEXT,  -- 'thuvienphapluat', 'luatindia'
  
  -- Metadata
  article_count INT,
  word_count INT,
  crawled_at TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE law_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  law_id UUID NOT NULL REFERENCES law_documents(id) ON DELETE CASCADE,
  
  -- Structure
  chapter TEXT,       -- "Chapter III"
  section TEXT,       -- "Section 2"
  article TEXT,       -- "iu 41"
  clause TEXT,        -- "Clause 2"
  point TEXT,         -- "im a"
  
  -- Content
  title TEXT,         -- Article title if any
  content TEXT NOT NULL,
  
  -- Context (for better retrieval)
  parent_context TEXT,  -- Parent article/section summary
  
  -- Embeddings
  embedding vector(1024),  -- BGE-M3 dense embedding
  
  -- Search
  search_vector tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(title, '') || ' ' || content)
  ) STORED,
  
  -- Metadata for filtering
  domains legal_domain[],
  keywords TEXT[],
  
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Cross-references between laws
CREATE TABLE law_relations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_law_id UUID REFERENCES law_documents(id),
  source_article TEXT,  -- "iu 41"
  target_law_id UUID REFERENCES law_documents(id),
  target_article TEXT,
  relation_type TEXT,  -- 'references', 'amends', 'replaces', 'guides'
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for law search
CREATE INDEX idx_law_chunks_embedding ON law_chunks 
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);
CREATE INDEX idx_law_chunks_search ON law_chunks USING gin(search_vector);
CREATE INDEX idx_law_chunks_law ON law_chunks(law_id);
CREATE INDEX idx_law_chunks_article ON law_chunks(article);
CREATE INDEX idx_law_chunks_domains ON law_chunks USING gin(domains);
CREATE INDEX idx_law_docs_number ON law_documents(law_number);
CREATE INDEX idx_law_docs_status ON law_documents(status);
CREATE INDEX idx_law_docs_domains ON law_documents USING gin(domains);
CREATE INDEX idx_law_docs_type ON law_documents(law_type);

-- ============================================
-- 3. CHAT & CONVERSATIONS
-- ============================================

CREATE TYPE agent_type AS ENUM ('qa', 'review', 'compliance', 'draft', 'research', 'general');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');

CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id),
  
  title TEXT,
  agent_type agent_type DEFAULT 'qa',
  status TEXT DEFAULT 'active',  -- active, archived, deleted
  
  -- Context
  metadata JSONB DEFAULT '{}',
  
  message_count INT DEFAULT 0,
  last_message_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  company_id UUID NOT NULL,  -- denormalized for RLS
  
  role message_role NOT NULL,
  content TEXT NOT NULL,
  
  -- AI metadata
  citations JSONB DEFAULT '[]',  -- [{law_id, article, text}]
  confidence FLOAT,
  tokens_used INT,
  model TEXT,
  
  -- Feedback
  feedback TEXT,  -- 'positive', 'negative'
  feedback_note TEXT,
  
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_sessions_company ON chat_sessions(company_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_company ON messages(company_id);

-- ============================================
-- 4. DOCUMENT MANAGEMENT
-- ============================================

CREATE TYPE doc_status AS ENUM ('uploaded', 'processing', 'analyzed', 'error');
CREATE TYPE doc_type AS ENUM (
  'hop_dong_lao_dong',    -- Labor contract
  'hop_dong_thuong_mai',  -- Commercial contract
  'hop_dong_dich_vu',     -- Service contract
  'noi_rule',              -- Internal rules
  'rule_che',              -- Regulations
  'ruleet_dinh',           -- Decision
  'other'
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  uploaded_by UUID REFERENCES users(id),
  
  name TEXT NOT NULL,
  file_path TEXT NOT NULL,  -- Supabase Storage path
  file_size INT,
  mime_type TEXT,
  
  doc_type doc_type,
  status doc_status DEFAULT 'uploaded',
  
  -- Extracted content
  extracted_text TEXT,
  page_count INT,
  
  -- Analysis results
  analysis JSONB,  -- Full review report
  risk_score INT,  -- 0-100
  issues_count INT DEFAULT 0,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  analyzed_at TIMESTAMPTZ
);

-- Company document chunks (for RAG with company context)
CREATE TABLE company_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  
  content TEXT NOT NULL,
  embedding vector(1024),
  metadata JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_documents_company ON documents(company_id);
CREATE INDEX idx_company_chunks_company ON company_chunks(company_id);
CREATE INDEX idx_company_chunks_embedding ON company_chunks 
  USING hnsw (embedding vector_cosine_ops);

-- ============================================
-- 5. USAGE & BILLING
-- ============================================

CREATE TABLE usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id),
  user_id UUID REFERENCES users(id),
  api_key_id UUID REFERENCES api_keys(id),
  
  -- What
  endpoint TEXT NOT NULL,  -- '/v1/legal/ask'
  agent_type agent_type,
  
  -- Cost
  input_tokens INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  embedding_tokens INT DEFAULT 0,
  total_cost_usd NUMERIC(10,6) DEFAULT 0,
  
  -- Performance
  latency_ms INT,
  status_code INT,
  
  -- Context
  request_metadata JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Monthly aggregation view
CREATE MATERIALIZED VIEW monthly_usage AS
SELECT 
  company_id,
  date_trunc('month', created_at) AS month,
  COUNT(*) AS total_requests,
  SUM(input_tokens) AS total_input_tokens,
  SUM(output_tokens) AS total_output_tokens,
  SUM(total_cost_usd) AS total_cost,
  AVG(latency_ms) AS avg_latency
FROM usage_logs
GROUP BY company_id, date_trunc('month', created_at);

CREATE INDEX idx_usage_company_date ON usage_logs(company_id, created_at);

-- ============================================
-- 6. ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on all tenant tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- Helper function
CREATE OR REPLACE FUNCTION get_user_company_id()
RETURNS UUID AS $$
  SELECT company_id FROM users WHERE id = auth.uid()
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- Companies: users see only their company
CREATE POLICY "users_own_company" ON companies
  FOR ALL USING (id = get_user_company_id());

-- Users: see only same company users
CREATE POLICY "same_company_users" ON users
  FOR ALL USING (company_id = get_user_company_id());

-- API Keys: company isolation
CREATE POLICY "company_api_keys" ON api_keys
  FOR ALL USING (company_id = get_user_company_id());

-- Chat sessions: company isolation
CREATE POLICY "company_sessions" ON chat_sessions
  FOR ALL USING (company_id = get_user_company_id());

-- Messages: company isolation
CREATE POLICY "company_messages" ON messages
  FOR ALL USING (company_id = get_user_company_id());

-- Documents: company isolation
CREATE POLICY "company_documents" ON documents
  FOR ALL USING (company_id = get_user_company_id());

-- Company chunks: company isolation
CREATE POLICY "company_chunks_policy" ON company_chunks
  FOR ALL USING (company_id = get_user_company_id());

-- Usage logs: company isolation
CREATE POLICY "company_usage" ON usage_logs
  FOR ALL USING (company_id = get_user_company_id());

-- Law documents: PUBLIC READ (shared resource)
ALTER TABLE law_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "law_public_read" ON law_documents FOR SELECT USING (true);

ALTER TABLE law_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "law_chunks_public_read" ON law_chunks FOR SELECT USING (true);

ALTER TABLE law_relations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "law_relations_public_read" ON law_relations FOR SELECT USING (true);

-- Service role bypass (for backend API server)
-- The FastAPI backend uses service_role key which bypasses RLS

-- ============================================
-- 7. FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER companies_updated_at
  BEFORE UPDATE ON companies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER law_documents_updated_at
  BEFORE UPDATE ON law_documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Increment message count on session
CREATE OR REPLACE FUNCTION increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE chat_sessions 
  SET message_count = message_count + 1,
      last_message_at = now()
  WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER messages_count_trigger
  AFTER INSERT ON messages
  FOR EACH ROW EXECUTE FUNCTION increment_message_count();

-- Increment used quota
CREATE OR REPLACE FUNCTION increment_quota()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE companies 
  SET used_quota = used_quota + 1
  WHERE id = NEW.company_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER usage_quota_trigger
  AFTER INSERT ON usage_logs
  FOR EACH ROW EXECUTE FUNCTION increment_quota();

-- Reset monthly quota
CREATE OR REPLACE FUNCTION reset_monthly_quotas()
RETURNS void AS $$
BEGIN
  UPDATE companies 
  SET used_quota = 0, 
      quota_reset_at = date_trunc('month', now()) + interval '1 month'
  WHERE quota_reset_at <= now();
END;
$$ LANGUAGE plpgsql;

-- Hybrid search function
CREATE OR REPLACE FUNCTION search_law_chunks(
  query_embedding vector(1024),
  query_text TEXT,
  filter_domains legal_domain[] DEFAULT NULL,
  match_count INT DEFAULT 10,
  semantic_weight FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id UUID,
  law_id UUID,
  article TEXT,
  clause TEXT,
  content TEXT,
  title TEXT,
  parent_context TEXT,
  domains legal_domain[],
  semantic_score FLOAT,
  keyword_score FLOAT,
  combined_score FLOAT,
  law_number TEXT,
  law_title TEXT,
  law_status law_status
) AS $$
BEGIN
  RETURN QUERY
  WITH semantic AS (
    SELECT 
      lc.id,
      1 - (lc.embedding <=> query_embedding) AS score
    FROM law_chunks lc
    WHERE (filter_domains IS NULL OR lc.domains && filter_domains)
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count * 3
  ),
  keyword AS (
    SELECT 
      lc.id,
      ts_rank_cd(lc.search_vector, plainto_tsquery('simple', query_text)) AS score
    FROM law_chunks lc
    WHERE lc.search_vector @@ plainto_tsquery('simple', query_text)
      AND (filter_domains IS NULL OR lc.domains && filter_domains)
    ORDER BY score DESC
    LIMIT match_count * 3
  ),
  combined AS (
    SELECT 
      COALESCE(s.id, k.id) AS chunk_id,
      COALESCE(s.score, 0) AS sem_score,
      COALESCE(k.score, 0) AS kw_score,
      COALESCE(s.score, 0) * semantic_weight + 
        COALESCE(k.score, 0) * (1 - semantic_weight) AS comb_score
    FROM semantic s
    FULL OUTER JOIN keyword k ON s.id = k.id
    ORDER BY comb_score DESC
    LIMIT match_count
  )
  SELECT 
    lc.id,
    lc.law_id,
    lc.article,
    lc.clause,
    lc.content,
    lc.title,
    lc.parent_context,
    lc.domains,
    c.sem_score,
    c.kw_score,
    c.comb_score,
    ld.law_number,
    ld.title AS law_title,
    ld.status AS law_status
  FROM combined c
  JOIN law_chunks lc ON lc.id = c.chunk_id
  JOIN law_documents ld ON ld.id = lc.law_id
  ORDER BY c.comb_score DESC;
END;
$$ LANGUAGE plpgsql;
```
