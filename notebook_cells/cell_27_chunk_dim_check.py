# Verbatim from cell 27 of notebooks/ingest_ticker_news_embeddings
# Before running the cells below, ensure you've manually run:
#   sql/03_setup_chunk_embeddings_table.sql
# Replace {{EMBEDDING_DIM}} in that file with the value below:
print(f"Required EMBEDDING_DIM for SQL setup: {EMBEDDING_DIM}")
print(f"Table name: {CHUNK_EMBEDDINGS_TABLE_NAME}")
print("\nRun sql/03_setup_chunk_embeddings_table.sql in your Lakebase database before continuing.")
