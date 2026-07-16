import os
"""
Load Indian legal documents into Supabase
- Parse law metadata from content
- Chunk documents for RAG
- Store in law_documents + law_chunks tables
"""
import json
import re
import psycopg2
import uuid
from typing import List, Dict, Optional

DB_CONFIG = {
    "host": os.getenv("SUPABASE_DB_HOST", "localhost"),
    "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("SUPABASE_DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSL_MODE", "require")
}

# Map dataset types to our enum
TYPE_MAP = {
    "constitution": "constitution",
    "act": "act", 
    "rules": "rules",
    "regulation": "regulation",
    "notification": "notification",
    "order": "order",
    "ordinance": "ordinance",
}

# Detect legal domain from title/content
DOMAIN_KEYWORDS = {
    "labour": ["labour", "employee", "wages", "industrial dispute", "factory"],
    "corporate": ["company", "director", "shareholder", "incorporation"],
    "civil": ["contract", "property", "tort", "succession"],
    "criminal": ["offence", "punishment", "bail", "FIR"],
    "tax": ["income tax", "GST", "customs", "excise"],
    "property": ["land", "registration", "transfer", "real estate"],
    "consumer": ["consumer", "product liability", "unfair trade"],
    "it_cyber": ["information technology", "cyber", "data protection", "electronic"],
}

def detect_domains(title: str, content: str) -> List[str]:
    """Detect legal domains from title and content (first 5000 chars)"""
    text = (title + " " + content[:5000]).lower()
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            domains.append(domain)
    return domains if domains else ["other"]

def extract_metadata(content: str) -> Dict:
    """Extract law number, issuer, dates from content"""
    meta = {"law_number": "", "issuer": "", "issued_date": None, "effective_date": None}
    
    # Try to find law number (S hiu)
    m = re.search(r'(?:S hiu|S)[:\s]*([^\n]+)', content[:2000])
    if m:
        meta["law_number"] = m.group(1).strip()
    
    # Try filename-based number
    if not meta["law_number"]:
        m = re.search(r'(\d+/\d{4}/[A-Z\-]+\d*)', content[:5000])
        if m:
            meta["law_number"] = m.group(1)
    
    # Issuer
    if "QUC HI" in content[:500]:
        meta["issuer"] = "Quc hi"
    elif "CHNH PH" in content[:500]:
        meta["issuer"] = "Government"
    elif "TH TNG" in content[:500]:
        meta["issuer"] = "Th tng Government"
    else:
        meta["issuer"] = "Undefined"
    
    # Effective date
    m = re.search(r'(?:Ngy hiu lc|c hiu lc)[:\s]*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', content[:3000])
    if m:
        date_str = m.group(1)
        if "-" in date_str:
            meta["effective_date"] = date_str
        else:
            parts = date_str.split("/")
            meta["effective_date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
    
    return meta

def chunk_document(content: str, chunk_size: int = 1500, overlap: int = 200) -> List[Dict]:
    """Split document into chunks, respecting article boundaries"""
    chunks = []
    
    # Try to split by articles (Article/Section)
    article_pattern = re.compile(r'(?:^|\n)((?:Article|Section)\s+\d+[A-Z]?\.?\s*[^\n]*)', re.MULTILINE)
    articles = list(article_pattern.finditer(content))
    
    if len(articles) > 3:
        # Split by articles
        for i, match in enumerate(articles):
            start = match.start()
            end = articles[i+1].start() if i+1 < len(articles) else len(content)
            article_text = content[start:end].strip()
            
            # Extract article number
            art_match = re.match(r'(?:iu|IU)\s+(\d+[a-z]?)', article_text)
            article_num = art_match.group(1) if art_match else str(i+1)
            
            # If article is too long, sub-chunk it
            if len(article_text) > chunk_size * 2:
                sub_chunks = simple_chunk(article_text, chunk_size, overlap)
                for j, sc in enumerate(sub_chunks):
                    chunks.append({
                        "article": f"iu {article_num}",
                        "clause": f"part {j+1}" if len(sub_chunks) > 1 else None,
                        "content": sc,
                        "title": match.group(1).strip()[:200]
                    })
            else:
                chunks.append({
                    "article": f"iu {article_num}",
                    "clause": None,
                    "content": article_text,
                    "title": match.group(1).strip()[:200]
                })
    else:
        # No articles found, simple chunking
        sub_chunks = simple_chunk(content, chunk_size, overlap)
        for i, sc in enumerate(sub_chunks):
            chunks.append({
                "article": None,
                "clause": None,
                "content": sc,
                "title": f"Part {i+1}"
            })
    
    return chunks

def simple_chunk(text: str, size: int = 1500, overlap: int = 200) -> List[str]:
    """Simple text chunking with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        # Try to break at paragraph
        if end < len(text):
            newline = text.rfind('\n', start + size - overlap, end + overlap)
            if newline > start:
                end = newline
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else len(text)
    return [c for c in chunks if len(c) > 50]  # Skip tiny chunks

def main():
    # Load processed data
    with open("/home/admin_1/projects/legal-ai-agent/data/uts_vlc_processed.json", "r") as f:
        docs = json.load(f)
    
    print(f"📥 Loading {len(docs)} documents into Supabase...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    total_chunks = 0
    loaded_docs = 0
    skipped = 0
    
    for i, doc in enumerate(docs):
        content = doc.get("content", "")
        if not content or len(content) < 100:
            skipped += 1
            continue
        
        title = doc.get("title", "Unknown")
        doc_type = TYPE_MAP.get(doc.get("type", ""), "luat")
        meta = extract_metadata(content)
        domains = detect_domains(title, content)
        
        law_number = meta["law_number"] or doc.get("id", f"unknown-{i}")
        
        # Insert law_document
        doc_id = str(uuid.uuid4())
        try:
            cur.execute("""
                INSERT INTO law_documents (id, title, law_number, law_type, issuer, 
                    effective_date, status, domains, full_text, source_site,
                    article_count, word_count)
                VALUES (%s, %s, %s, %s, %s, %s, 'active', %s, %s, 'huggingface/UTS_VLC',
                    %s, %s)
            """, (
                doc_id, title, law_number, doc_type, meta["issuer"],
                meta["effective_date"], domains, content,
                len(re.findall(r'(?:iu|IU)\s+\d+', content)),
                len(content.split())
            ))
        except Exception as e:
            print(f"  ❌ Doc {i} ({title[:30]}): {str(e)[:80]}")
            conn.rollback()
            conn.autocommit = True
            continue
        
        # Chunk and insert
        chunks = chunk_document(content)
        for chunk in chunks:
            try:
                cur.execute("""
                    INSERT INTO law_chunks (law_id, article, clause, title, content, domains)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    doc_id, chunk["article"], chunk["clause"],
                    chunk["title"], chunk["content"], domains
                ))
                total_chunks += 1
            except Exception as e:
                pass
        
        loaded_docs += 1
        if (i+1) % 50 == 0:
            print(f"  📊 Progress: {i+1}/{len(docs)} docs, {total_chunks} chunks")
    
    # Final stats
    cur.execute("SELECT COUNT(*) FROM law_documents;")
    doc_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM law_chunks;")
    chunk_count = cur.fetchone()[0]
    
    print(f"\n🏆 LOAD COMPLETE!")
    print(f"  📄 Documents: {doc_count}")
    print(f"  📦 Chunks: {chunk_count}")
    print(f"  ⏭️ Skipped: {skipped} (empty)")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
