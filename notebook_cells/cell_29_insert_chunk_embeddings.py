# Converted from cell 29 ("Insert chunk embeddings") of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute)
import ssl
from datetime import datetime

import pg8000.dbapi

# Add id (article_id_chunk_index), model_name, and embedded_at columns
chunk_embeddings_df['id'] = chunk_embeddings_df['article_id'] + '_' + chunk_embeddings_df['chunk_index']
chunk_embeddings_df['model_name'] = EMBEDDING_MODEL_NAME
chunk_embeddings_df['embedded_at'] = datetime.now()
chunk_embeddings_df['chunk_index'] = chunk_embeddings_df['chunk_index'].astype(int)

chunk_embeddings_rows = chunk_embeddings_df.to_dict('records')

if len(chunk_embeddings_rows) > 0:
    print(f"Inserting {len(chunk_embeddings_rows)} chunk embeddings into {CHUNK_EMBEDDINGS_TABLE_NAME}...")
    
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
        # Format embedding as PostgreSQL array literal: '{val1,val2,...}'
        insert_data = [
            (
                row['id'],
                row['article_id'],
                row['ticker'],
                int(row['chunk_index']),
                row['chunk_text'],
                '{' + ','.join(str(float(x)) for x in row['embedding']) + '}',
                row['model_name'],
                row['embedded_at']
            )
            for row in chunk_embeddings_rows
        ]
        
        # Batch insert with ON CONFLICT DO NOTHING for deduplication
        insert_sql = f"""
            INSERT INTO {CHUNK_EMBEDDINGS_TABLE_NAME} (
                id, article_id, ticker, chunk_index, chunk_text, embedding, model_name, embedded_at
            ) VALUES (%s, %s, %s, %s, %s, %s::double precision[], %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        
        # executemany batches the INSERTs efficiently
        cursor.executemany(insert_sql, insert_data)
        
        conn.commit()
        inserted_count = cursor.rowcount
        print(f"✅ Successfully inserted {inserted_count} new chunk embeddings")
        print(f"   (Duplicates were skipped via ON CONFLICT DO NOTHING)")
        print("\nIMPORTANT: Run this SQL in your Lakebase database to cast arrays to vectors:")
        print(f"  UPDATE {CHUNK_EMBEDDINGS_TABLE_NAME} SET embedding = embedding::vector WHERE embedding IS NOT NULL;")
        
    finally:
        cursor.close()
        conn.close()
else:
    print("No chunk embeddings to write.")
