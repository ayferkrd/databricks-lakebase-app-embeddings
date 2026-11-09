# Converted from cell 13 ("Insert collected news articles") of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute)
import ssl

import pg8000.dbapi

# Build connection using pg8000
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
    cursor = conn.cursor()
    
    # Prepare data tuples for batch insert
    insert_data = [
        (
            row['id'],
            row['ticker'],
            row['title'],
            row['description'],
            row['author'],
            row['article_url'],
            row['publisher_name'],
            row['keywords'],
            row['sentiment'],
            row['sentiment_reasoning'],
            row['published_utc'],
            row['payload']
        )
        for row in all_news_rows
    ]
    
    # Batch insert with ON CONFLICT DO NOTHING for deduplication
    insert_sql = f"""
        INSERT INTO {NEWS_TABLE_NAME} (
            id, ticker, title, description, author, article_url, publisher_name,
            keywords, sentiment, sentiment_reasoning, published_utc, payload, synced_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """
    
    # executemany batches the INSERTs efficiently
    cursor.executemany(insert_sql, insert_data)
    
    conn.commit()
    inserted_count = cursor.rowcount
    print(f"✅ Successfully inserted {inserted_count} new news articles")
    print(f"   (Duplicates were skipped via ON CONFLICT DO NOTHING)")
    
finally:
    cursor.close()
    conn.close()

print(f"\nReady to compute embeddings! Run the cells below to continue.")
