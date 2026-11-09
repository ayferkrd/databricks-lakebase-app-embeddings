# Converted from cell 9 ("Test Psycopg2 connection") of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute)
import ssl

import pg8000.dbapi

print(f"Testing connection to {db_host}:{db_port}/{db_name}")
print(f"Using credentials from the lakebase-url secret as user: {db_user}\n")

# Test pg8000 connection to Lakebase
try:
    conn = pg8000.dbapi.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        ssl_context=ssl.create_default_context(),
        timeout=10
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {WATCHLIST_TABLE_NAME}")
    count = cursor.fetchone()[0]
    print(f"✅ Connection successful! Found {count} rows in {WATCHLIST_TABLE_NAME}")
    
    cursor.execute(f"SELECT * FROM {WATCHLIST_TABLE_NAME} LIMIT 5")
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    print(f"\nColumns: {colnames}")
    for row in rows:
        print(row)
    
    cursor.close()
    conn.close()
    print("\n✅ pg8000 connection working correctly!")
except Exception as e:
    import traceback
    print(f"❌ Connection failed: {e}")
    print(f"\nFull traceback:")
    traceback.print_exc()
