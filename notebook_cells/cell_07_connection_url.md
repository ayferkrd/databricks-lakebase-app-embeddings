## Resolve the Lakebase connection URL

Same secret, same decoding scheme as `lakebase.py`: a single base64-encoded
Postgres URL (`postgresql://role:password@host:5432/db?sslmode=require`)
stored in a Databricks secret scope. We parse it into the pieces psycopg3
needs for connection (host/port/dbname/user/password).
