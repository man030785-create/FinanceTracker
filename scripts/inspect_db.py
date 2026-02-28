"""
One-off script to inspect Postgres tables. Run from project root with Render DATABASE_URL in .env:
  python scripts/inspect_db.py
Or set DATABASE_URL in the environment.
"""
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "sqlite" in DATABASE_URL:
    print("Set DATABASE_URL to your Postgres URL (e.g. Render Internal Database URL) in .env")
    sys.exit(1)

# Normalize postgres:// -> postgresql:// and add sslmode if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://") :]
if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require" if "?" not in DATABASE_URL else "&sslmode=require"

import psycopg2
from psycopg2 import sql

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    # List tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print("Tables:", tables)
    for table in tables:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
        n = cur.fetchone()[0]
        print(f"  {table}: {n} rows")
        if n > 0 and n <= 20:
            cur.execute(sql.SQL("SELECT * FROM {} LIMIT 5").format(sql.Identifier(table)))
            cols = [d[0] for d in cur.description]
            print(f"    Columns: {cols}")
            for row in cur.fetchall():
                row_str = list(row)
                if "hashed_password" in cols:
                    i = cols.index("hashed_password")
                    row_str[i] = "***" if row_str[i] else None
                print(f"    {row_str}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
