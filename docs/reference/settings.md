# Settings and logging

FastPG relies on a handful of environment variables to configure database
connections, timestamp behaviour, and SQL logging.

## Database connections

Two connection pools are created automatically when you import `fastpg.db`:

- `ASYNC_DB_READ` – read-only operations
- `ASYNC_DB_WRITE` – write operations wrapped in transactions

Provide credentials via the following environment variables:

| Variable | Description |
|----------|-------------|
| `POSTGRES_READ_USER` / `POSTGRES_WRITE_USER` | Database user for each pool. |
| `POSTGRES_READ_PASSWORD` / `POSTGRES_WRITE_PASSWORD` | Password for the user. |
| `POSTGRES_READ_DB` / `POSTGRES_WRITE_DB` | Database name. |
| `POSTGRES_READ_HOST` / `POSTGRES_WRITE_HOST` | Hostname or IP address. |
| `POSTGRES_READ_PORT` / `POSTGRES_WRITE_PORT` | Port number. |

Connections are established lazily when you call `connect()`. Each pool uses an
asyncpg-powered DSN with a minimum of two connections and a maximum of five.

## Timezone

`FASTPG_TZ` controls the timezone for automatic timestamp fields. Unknown values
fall back to UTC.

## SQL logging

Set `LOG_DB_QUERIES=true` to log the SQL statement and execution time for every
query executed through `AsyncPostgresDB`. The logger categorises durations into
<1s, 1–5s, 5–10s, and >10s buckets and prefixes the message with the upper-cased
`PROJECT_NAME` (defaults to `UNNAMED`). Use standard Python logging
configuration to route these logs to stdout, files, or observability systems.
