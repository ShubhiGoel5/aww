import json
import uuid
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': int(os.getenv('SUPABASE_DB_PORT', '6543')),
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
    'sslmode': os.getenv('DB_SSL_MODE', 'require')
}

def load_ipc():
    with open('data/indian_penal_code.json', 'r', encoding='utf-8') as f:
        sections = json.load(f)

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    doc_id = str(uuid.uuid4())
    # Insert main law document
    cur.execute("""
        INSERT INTO law_documents (id, title, law_number, law_type, issuer, status, domains, article_count, source_site)
        VALUES (%s, 'Indian Penal Code, 1860', '45 of 1860', 'act', 'Parliament of India', 'active', ARRAY['criminal'], %s, 'local')
    """, (doc_id, len(sections)))

    print(f'Inserted Indian Penal Code with {len(sections)} sections.')

    # Insert chunks
    for sec in sections:
        chunk_id = str(uuid.uuid4())
        chapter = f"Chapter {sec.get('chapter')}: {sec.get('chapter_title')}"
        section_number = f"Section {sec.get('Section')}"
        title = sec.get('section_title', '')
        content = sec.get('section_desc', '')
        
        # We don't have embeddings right now, so we leave it NULL
        cur.execute("""
            INSERT INTO law_chunks (id, law_id, chapter, section, title, content, domains)
            VALUES (%s, %s, %s, %s, %s, %s, ARRAY['criminal'])
        """, (chunk_id, doc_id, chapter, section_number, title, content))

    print('Successfully inserted all chunks!')
    cur.close()
    conn.close()

if __name__ == '__main__':
    load_ipc()
