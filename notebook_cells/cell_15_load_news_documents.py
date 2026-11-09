# Converted from cell 15 of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute)
import ssl

import pandas as pd
import pg8000.dbapi

# Load news documents using pg8000
conn = pg8000.dbapi.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password,
    ssl_context=ssl.create_default_context(),
    timeout=10
)

try:
    # Query with embedding_text computed
    query = f"""
        SELECT 
            id,
            ticker,
            title,
            description,
            article_url,
            published_utc,
            TRIM(CONCAT(COALESCE(title, ''), '. ', COALESCE(description, ''))) AS embedding_text
        FROM {NEWS_TABLE_NAME}
        WHERE TRIM(CONCAT(COALESCE(title, ''), '. ', COALESCE(description, ''))) IS NOT NULL
          AND TRIM(CONCAT(COALESCE(title, ''), '. ', COALESCE(description, ''))) != ''
    """
    
    news_df = pd.read_sql_query(query, conn)
    print(f"Loaded {len(news_df)} news documents from {NEWS_TABLE_NAME}")
    display(news_df.head(5))
finally:
    conn.close()
