# Verbatim from cell 2 ("Install all required packages") of notebooks/ingest_ticker_news_embeddings
%pip uninstall -y psycopg2 psycopg2-binary
%pip install -q 'databricks-sdk>=0.118.0' sentence-transformers trafilatura requests pandas
