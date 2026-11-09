"""Python setup script for the Lakebase tables used by the
`ingest_ticker_news_embeddings` notebook.

Runs the equivalent of the SQL files in this folder:

- 01_setup_news_table.sql             -> ticker_news_documents
- 02_setup_embeddings_table.sql      -> ticker_news_embeddings (pgvector)
- 03_setup_chunk_embeddings_table.sql -> ticker_news_chunk_embeddings

Unlike the .sql files, this script needs no psql and no psycopg2 install:
it talks to Lakebase with `pg8000` (a pure-Python Postgres driver), so it
runs fine on Serverless notebooks, classic clusters, and your laptop.

Usage (notebook cell):

    %pip install -q pg8000
    %run ../sql/setup_lakebase_tables.py

Usage (local shell, with Databricks CLI configured):

    pip install pg8000 databricks-sdk
    python setup_lakebase_tables.py

Everything is idempotent (IF NOT EXISTS), so re-running is safe.
"""

import base64
import ssl
from urllib.parse import urlparse

import pg8000.dbapi
from databricks.sdk import WorkspaceClient

# Connection secret - same one the notebook and the Flask app use.
SECRET_SCOPE = "database"
SECRET_KEY = "lakebase-url"

# Vector dimension for the pgvector VECTOR(N) columns. Defaults to 384
# (sentence-transformers/all-MiniLM-L6-v2). When run from the notebook via
# %run, the notebook's EMBEDDING_DIM (from the embedding_model widget) is
# picked up automatically. Must match the model the notebook uses, and the
# tables must be empty (or recreated) if you change it later.
EMBEDDING_DIM = int(globals().get("EMBEDDING_DIM", 384))


def get_connection() -> "pg8000.dbapi.Connection":
    """Connect to Lakebase using the base64-encoded URL from the secret."""
    secret = WorkspaceClient().secrets.get_secret(scope=SECRET_SCOPE, key=SECRET_KEY)
    url = base64.b64decode(secret.value).decode("utf-8")
    parsed = urlparse(url)
    return pg8000.dbapi.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        ssl_context=ssl.create_default_context(),
        timeout=10,
    )


DDL_STATEMENTS = [
    # 01_setup_news_table.sql
    """CREATE TABLE IF NOT EXISTS ticker_news_documents (
        id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        author TEXT,
        article_url TEXT,
        publisher_name TEXT,
        keywords JSONB,
        sentiment TEXT,
        sentiment_reasoning TEXT,
        published_utc TIMESTAMPTZ,
        payload JSONB NOT NULL,
        synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE INDEX IF NOT EXISTS idx_ticker_news_documents_ticker
    ON ticker_news_documents (ticker)""",
    # 02_setup_embeddings_table.sql ({{EMBEDDING_DIM}} substituted)
    """CREATE TABLE IF NOT EXISTS ticker_news_embeddings (
        id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        title TEXT NOT NULL,
        published_utc TIMESTAMPTZ,
        embedding VECTOR({dim}) NOT NULL,
        model_name TEXT NOT NULL,
        embedded_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE INDEX IF NOT EXISTS idx_ticker_news_embeddings_embedding
    ON ticker_news_embeddings
    USING hnsw (embedding vector_cosine_ops)""",
    # 03_setup_chunk_embeddings_table.sql ({{EMBEDDING_DIM}} substituted)
    """CREATE TABLE IF NOT EXISTS ticker_news_chunk_embeddings (
        id TEXT PRIMARY KEY,
        article_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        chunk_index INT NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding VECTOR({dim}) NOT NULL,
        model_name TEXT NOT NULL,
        embedded_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE INDEX IF NOT EXISTS idx_ticker_news_chunk_embeddings_embedding
    ON ticker_news_chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)""",
]


def main() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # pgvector must be enabled before VECTOR(N) columns can be created.
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        print("pgvector extension enabled")

        print(f"Creating tables/indexes with VECTOR({EMBEDDING_DIM}) columns ...")
        for stmt in DDL_STATEMENTS:
            cursor.execute(stmt.format(dim=EMBEDDING_DIM))
            conn.commit()

        # Verification - same queries as in the .sql files.
        for table in (
            "ticker_news_documents",
            "ticker_news_embeddings",
            "ticker_news_chunk_embeddings",
        ):
            cursor.execute(
                """SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position""",
                (table,),
            )
            cols = cursor.fetchall()
            print(f"\n{table} ({len(cols)} columns):")
            for name, dtype in cols:
                print(f"  {name} - {dtype}")

        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        print(f"\npgvector version: {cursor.fetchone()[0]}")
        print("\nSetup complete - all three tables are ready.")
    finally:
        conn.close()


main()
