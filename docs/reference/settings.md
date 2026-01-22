# Settings and logging

FastPG uses a Python-first configuration API to define database connections,
timezone handling, and SQL logging.

## Database configuration

Create a FastPG instance with `create_fastpg` and pass a `databases` mapping.
Each entry is a named connection with a `TYPE` (read/write) and credentials.

```python
import os
from fastpg import create_fastpg, ConnectionType

FAST_PG = create_fastpg(
    name="default",
    databases={
        "primary": {
            "TYPE": ConnectionType.WRITE,
            "USER": os.environ["POSTGRES_WRITE_USER"],
            "PASSWORD": os.environ["POSTGRES_WRITE_PASSWORD"],
            "DB": os.environ["POSTGRES_WRITE_DB"],
            "HOST": os.environ["POSTGRES_WRITE_HOST"],
            "PORT": os.environ["POSTGRES_WRITE_PORT"],
        },
        "replica_1": {
            "TYPE": ConnectionType.READ,
            "USER": os.environ["POSTGRES_READ_USER"],
            "PASSWORD": os.environ["POSTGRES_READ_PASSWORD"],
            "DB": os.environ["POSTGRES_READ_DB"],
            "HOST": os.environ["POSTGRES_READ_HOST"],
            "PORT": os.environ["POSTGRES_READ_PORT"],
        },
    },
)
```

Connections are established when you call `connect_all()` on the connection
manager. Each pool uses an asyncpg-powered DSN with a minimum of two
connections and a maximum of five.

## Connection routing

FastPG routes reads and writes based on connection type:

- reads use a random `ConnectionType.READ` connection
- writes always use the single `ConnectionType.WRITE` connection

You must configure at least one read connection and exactly one write
connection. FastPG raises errors if a read connection is missing or multiple
write connections are supplied.

To target a specific connection, use `using()` on a queryset:

```python
orders = await Order.async_queryset.using("replica_1").filter(status="open")
```

## Timezone

Pass `tz_name` to `create_fastpg` to control automatic timestamp fields.
Unknown values fall back to UTC.

## SQL logging

Enable SQL timing logs by passing a `query_logger` dictionary to `create_fastpg`:

```python
FAST_PG = create_fastpg(
    databases=...,
    query_logger={
        "LOG_QUERIES": True,
        "TITLE": "MY_SERVICE",
    },
)
```

The logger categorises durations into <1s, 1–5s, 5–10s, and >10s buckets and
prefixes messages with the configured `TITLE`. Use standard Python logging
configuration to route these logs to stdout, files, or observability systems.
