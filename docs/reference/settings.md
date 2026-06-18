# Settings And Configuration

## `create_fastpg(...)`

Primary entry point:

```python
from fastpg import create_fastpg

create_fastpg(
    name="default",
    databases={...},
    tz_name="UTC",
    query_logger={"LOG_QUERIES": True, "TITLE": "MY_APP"},
    db_conn_manager_class=None,
)
```

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
from fastpg import ConnectionType

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
```

Validation behavior:

- At least one read connection is required.
- More than one write connection raises `MultipleWriteConnectionsError`.

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
