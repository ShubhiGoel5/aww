import os
#!/usr/bin/env python3
"""
Run migration_v1.sql on Supabase database
"""
import psycopg2
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("SUPABASE_DB_HOST", "localhost"),
    "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("SUPABASE_DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSL_MODE", "require")
}

def run_migration():
    try:
        # Read migration file
        with open("database/init.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        
        # Connect and execute
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Enabling extensions first...")
        cur.execute('SET search_path TO "$user", public, extensions;')
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        conn.commit()
        
        print("Running migration...")
        cur.execute('SET search_path TO "$user", public, extensions;\n' + sql)
        conn.commit()
        
        print("Migration completed successfully!")
        
        # Verify
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('auth_id', 'password_hash', 'user_settings')")
        results = cur.fetchall()
        print(f"Verified columns added to users table: {[r[0] for r in results]}")
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'company_invites'")
        if cur.fetchone():
            print("Verified company_invites table created")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
