# Converted from cell 12 ("Fetch news and sync using Lakebase SDK") of notebooks/ingest_ticker_news_embeddings
# (psycopg2 -> pg8000: pure-Python Postgres driver, safe on Serverless compute)
import base64 as _b64
import json as _json
import ssl
import time
from datetime import datetime

import pg8000.dbapi
import requests


def get_massive_api_key() -> str:
    secret = w.secrets.get_secret(scope=MASSIVE_SECRET_SCOPE, key=MASSIVE_SECRET_KEY)
    return _b64.b64decode(secret.value).decode("utf-8")


def get_watchlist_tickers() -> list[str]:
    """Distinct, uppercased ticker symbols currently tracked across all users
    in the watchlist table - these are the only tickers we fetch news for."""
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
        cursor.execute(f"SELECT DISTINCT symbol FROM {WATCHLIST_TABLE_NAME} WHERE symbol IS NOT NULL")
        symbols = cursor.fetchall()
        return [row[0].strip().upper() for row in symbols if row[0]]
    finally:
        cursor.close()
        conn.close()


def fetch_news_for_ticker(session: requests.Session, ticker: str, limit: int) -> list[dict]:
    """Single GET /v2/reference/news call for one ticker (mirrors
    MassiveClient.get_news in massive_client.py)."""
    resp = session.get(
        f"{MASSIVE_API_BASE_URL}/v2/reference/news",
        params={"ticker": ticker, "limit": limit, "order": "desc", "sort": "published_utc"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def sync_news_to_lakebase(ticker: str, articles: list[dict]) -> int:
    """Convert Massive API response and insert via Lakebase SDK executeLakebasePostgresSql tool.
    Uses ON CONFLICT DO NOTHING for automatic deduplication."""
    if not articles:
        return 0
    
    rows = []
    for article in articles:
        sentiment = None
        sentiment_reasoning = None
        for insight in article.get("insights", []) or []:
            if insight.get("ticker") == ticker:
                sentiment = insight.get("sentiment")
                sentiment_reasoning = insight.get("sentiment_reasoning")
                break

        publisher = article.get("publisher") or {}
        rows.append({
            "id": str(article.get("id")),
            "ticker": ticker,
            "title": article.get("title", ""),
            "description": article.get("description"),
            "author": article.get("author"),
            "article_url": article.get("article_url"),
            "publisher_name": publisher.get("name"),
            "keywords": _json.dumps(article.get("keywords", [])),
            "sentiment": sentiment,
            "sentiment_reasoning": sentiment_reasoning,
            "published_utc": article.get("published_utc"),
            "payload": _json.dumps(article),
        })

    # We'll collect these rows and write them via the assistant's executeLakebasePostgresSql tool
    # Store in a global so the next cell can access them
    return rows


print("NOTE: Before running this cell, ensure you've run sql/01_setup_news_table.sql")
print("      to create the ticker_news_documents table in your Lakebase database.\n")

tickers = get_watchlist_tickers()
print(f"Found {len(tickers)} distinct watchlisted tickers: {tickers}")

# Enforce MAX_REQUESTS_PER_MINUTE by spacing calls evenly across a minute -
# e.g. 5/min -> one request every 12s. Sleeping BEFORE each call after the
# first keeps this correct even if a single request itself takes a while.
_seconds_between_requests = 60.0 / MAX_REQUESTS_PER_MINUTE

_massive_session = requests.Session()
_massive_session.headers.update(
    {"Authorization": f"Bearer {get_massive_api_key()}", "Content-Type": "application/json"}
)

news_synced = 0
all_news_rows = []  # Collect all rows to insert via Lakebase SDK
for i, ticker in enumerate(tickers):
    if i > 0:
        time.sleep(_seconds_between_requests)
    try:
        articles = fetch_news_for_ticker(_massive_session, ticker, NEWS_FETCH_LIMIT)
        batch_rows = sync_news_to_lakebase(ticker, articles)
        if batch_rows:
            all_news_rows.extend(batch_rows)
    except Exception as exc:
        print(f"Skipping {ticker}: failed to fetch/sync news ({exc})")
        continue

print(f"\nCollected {len(all_news_rows)} news articles to insert via Lakebase SDK.")
print(f"Run the next cell to insert them using executeLakebasePostgresSql tool.")
