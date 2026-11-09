# Verbatim from cell 23 of notebooks/ingest_ticker_news_embeddings
import pandas as pd
import requests
import trafilatura

# Filter news_df for articles with URLs
content_df = news_df[news_df['article_url'].notna() & (news_df['article_url'] != '')].copy()

print(f"Fetching and chunking content from {len(content_df)} article URLs...")

# Fetch and chunk article content
out_article_ids, out_tickers, out_chunk_indexes, out_chunk_texts = [], [], [], []

for idx, row in content_df.iterrows():
    article_id = row['id']
    ticker = row['ticker']
    article_url = row['article_url']
    
    try:
        resp = requests.get(article_url, timeout=15)
        resp.raise_for_status()
        text = trafilatura.extract(resp.text)
    except Exception as e:
        # Dead link, paywall, timeout, etc. - skip this article's
        # content chunks rather than failing the whole job.
        continue

    if not text:
        continue

    # Split into overlapping chunks
    for chunk_index, start in enumerate(range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP)):
        chunk_text = text[start : start + CHUNK_SIZE].strip()
        if not chunk_text:
            continue
        out_article_ids.append(article_id)
        out_tickers.append(ticker)
        out_chunk_indexes.append(str(chunk_index))
        out_chunk_texts.append(chunk_text)
        if start + CHUNK_SIZE >= len(text):
            break
    
    # Progress update every 10 articles
    if (idx + 1) % 10 == 0:
        print(f"  Processed {idx + 1}/{len(content_df)} articles")

chunks_df = pd.DataFrame({
    "article_id": out_article_ids,
    "ticker": out_tickers,
    "chunk_index": out_chunk_indexes,
    "chunk_text": out_chunk_texts,
})

print(f"Extracted {len(chunks_df)} content chunks from {len(content_df)} article URLs")
display(chunks_df.head(5))
