## Upsert embeddings into Lakebase

Written in batches via psycopg2's `executemany` for throughput.
Each embedding is cast to Postgres' `vector` type via `::vector`.
