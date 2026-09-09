# Settings And Configuration

## `create_fastpg(...)`

Primary entry point for configuring, registering, and selecting a FastPG instance.
It does not open database connections; call `await FAST_PG.db_conn_manager.connect_all()`
before running queries.

FastPG does not load environment variables by itself. Your application is responsible for building the `databases` config dict.

## Database Config Format

Each configured connection uses:

- `TYPE`: `ConnectionType.READ` or `ConnectionType.WRITE`
- `USER`
- `PASSWORD`
- `DB`
- `HOST`
- `PORT`

Example:

```python
from fastpg import ConnectionType, create_fastpg

databases = {
    "default": {
        "TYPE": ConnectionType.WRITE,
        "USER": "postgres",
        "PASSWORD": "postgres",
        "DB": "app_db",
        "HOST": "127.0.0.1",
        "PORT": 5432,
    },
    "replica_1": {
        "TYPE": ConnectionType.READ,
        "USER": "postgres",
        "PASSWORD": "postgres",
        "DB": "app_db",
        "HOST": "127.0.0.1",
        "PORT": 5433,
    },
}

FAST_PG = create_fastpg(
    name="default",
    databases=databases,
    tz_name="UTC",
    query_logger={"LOG_QUERIES": True, "TITLE": "MY_APP"},
    db_conn_manager_class=None,
)
```

Validation behavior:

- At least one read connection is required.
- More than one write connection raises `MultipleWriteConnectionsError`.
- Configure exactly one write connection; omitting it fails when connections
  are opened or a write connection is requested.

Read and write entries may point to the same server. The example connection
name `default` identifies the primary; it is not a reserved name in FastPG.

## Timezone

- `tz_name` controls the timezone used by auto timestamp preprocessors.
- Invalid timezone names fall back to `UTC`.

## Query Logging

Enable DB timing logs with:

```python
query_logger = {
    "LOG_QUERIES": True,
    "TITLE": "SHOP_API",
}
```

When enabled, FastPG logs through `fastpg.utils` and prefixes entries with the configured title plus an elapsed-time bucket.

## Registry Helpers

FastPG supports multiple named instances:

- `register_fastpg(name, instance)`
- `create_fastpg(name=...)`
- `get_fastpg(name=None)`
- `set_current_fastpg(name)`

`get_fastpg()` without a name uses the current context-bound instance.
`create_fastpg()` selects the new instance in the current context;
`register_fastpg()` only stores it. Select the intended instance before building
querysets. Already-fetched objects retain their originating write connection.

## `DBConnectionManager`

Methods:

- `connect_all()`
- `close_all()`
- `get_db_conn(conn_name)`
- `db_for_read()`
- `db_for_write()`

Routing behavior:

- `db_for_read()` randomly selects one configured read connection.
- `db_for_write()` always returns the single configured write connection.
- Querysets capture these connections when constructed. `.using(conn_name)`
  changes their read connection only; `lock_for_update()` always reads on their writer.
