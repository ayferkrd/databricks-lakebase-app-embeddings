# Ingest Ticker News -> Vector Embeddings (Lakebase)

This notebook is part of the **Context Engineering on Databricks** course.

It:
1. Reads the `watchlist` table in Lakebase to find out which ticker
   symbols are currently being tracked.
2. Fetches recent news for those tickers directly from the Massive
   `/v2/reference/news` endpoint (see `massive_client.py` for the same
   call shape used by the Flask app's `POST /news/sync` route), rate
   limited to stay within the free Massive API tier's strict quota, and
   upserts the results into the `ticker_news_documents` table.
3. Computes a sentence embedding for each article (title + description)
   using Spark, distributed across the cluster via a pandas UDF, and
   writes them into a `ticker_news_embeddings` table using the
   `pgvector` Postgres extension so downstream RAG / context-engineering
   exercises can run similarity search directly in Postgres.
4. Fetches the full article body for each `article_url` (via
   `trafilatura`, which strips nav/ads/boilerplate from the raw HTML),
   splits it into overlapping text chunks, embeds each chunk, and writes
   them into a `ticker_news_chunk_embeddings` table - so RAG exercises can
   retrieve fine-grained passages from article bodies, not just
   title/description.

It re-uses the SAME Lakebase secret (scope `database`, key `lakebase-url`)
that `lakebase.py` uses in the Flask app, so no extra secrets need to be
created for this notebook.
