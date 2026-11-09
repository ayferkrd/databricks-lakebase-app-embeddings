## Database Setup Instructions

Before running this notebook, you must manually create the required tables
in your Lakebase Postgres database:

1. Run `sql/01_setup_news_table.sql` to create `ticker_news_documents`
2. Run `sql/02_setup_embeddings_table.sql` to create `ticker_news_embeddings`
   - Replace `{{EMBEDDING_DIM}}` with your model's dimension (e.g., 384)
3. Run `sql/03_setup_chunk_embeddings_table.sql` to create `ticker_news_chunk_embeddings`
   - Replace `{{EMBEDDING_DIM}}` with your model's dimension (e.g., 384)

This notebook uses psycopg2 with OAuth token authentication for all database operations.

(Note: `sql/setup_lakebase_tables.py` is the one-step Python equivalent of
steps 1-3, runnable from a notebook via `%run`.)
