## Fetch news from Massive for watchlisted tickers

This ETL is now self-contained: instead of relying on the Flask app's
`POST /news/sync` route to have populated `ticker_news_documents` ahead of
time, the notebook queries the `watchlist` table in Lakebase directly to
find out which tickers are being tracked, then pulls news for exactly
those tickers from Massive itself.

The free Massive API tier is rate-limited very aggressively, so requests
are made **serially** (not distributed across Spark workers) with a sleep
between calls that enforces `MAX_REQUESTS_PER_MINUTE` (default 5/min).
