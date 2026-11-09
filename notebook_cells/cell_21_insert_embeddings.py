# Converted from cell 21 ("Insert embeddings") of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute;
#  pg8000 has no execute_values, so the batch insert uses executemany)
import ssl
from datetime import datetime

import pg8000.dbapi

# Add model_name and embedded_at columns
embeddings_df['model_name'] = EMBEDDING_MODEL_NAME
embeddings_df['embedded_at'] = datetime.now()

embeddings_rows = embeddings_df.to_dict('records')

if len(embeddings_rows) > 0:
    print(f"Inserting {len(embeddings_rows)} embeddings into {EMBEDDINGS_TABLE_NAME}...")
    
    # Build connection from parsed URL
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
        # Format embedding as PostgreSQL array literal: '{val1,val2,...}'
        insert_data = [
            (
                row['id'],
                row['ticker'],
                row['title'],
                str(row['published_utc']) if row['published_utc'] else None,
                '{' + ','.join(str(float(x)) for x in row['embedding']) + '}',
                row['model_name'],
                row['embedded_at']
            )
            for row in embeddings_rows
        ]
        
        # Batch insert with ON CONFLICT DO NOTHING for deduplication
        # (pg8000's executemany batches the rows over the wire)
        insert_sql = f"""
            INSERT INTO {EMBEDDINGS_TABLE_NAME} (
                id, ticker, title, published_utc, embedding, model_name, embedded_at
            ) VALUES (%s, %s, %s, %s, %s::double precision[], %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        
        cursor.executemany(insert_sql, insert_data)
        
        conn.commit()
        inserted_count = cursor.rowcount
        print(f"✅ Successfully inserted {inserted_count} new embeddings")
        print(f"   (Duplicates were skipped via ON CONFLICT DO NOTHING)")
        print("\nIMPORTANT: Run this SQL in your Lakebase database to cast arrays to vectors:")
        print(f"  UPDATE {EMBEDDINGS_TABLE_NAME} SET embedding = embedding::vector WHERE embedding IS NOT NULL;")
        
    finally:
        cursor.close()
        conn.close()
else:
    print("No embeddings to write.")
