# Settings And Configuration

## `create_fastpg(...)`

Primary entry point:

```python
create_fastpg(
    name="default",
    databases={...},
    tz_name="UTC",
    query_logger={"LOG_QUERIES": True, "TITLE": "MY_APP"},
    db_conn_manager_class=None,
)
```

## Databases config format

Each connection entry contains:

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

## Timezone

- `tz_name` controls timezone for automatic timestamp processors.
- Invalid timezone names fallback to `UTC`.

## Query logging

Enable DB timing logs:

```python
query_logger={
    "LOG_QUERIES": True,
    "TITLE": "SHOP_API",
}
```

When enabled, logs are emitted from `fastpg.utils` and bucketed by elapsed time.

## Registry helpers

FastPG supports multiple named instances:

- `register_fastpg(name, instance)`
- `create_fastpg(name=...)`
- `get_fastpg(name=None)`
- `set_current_fastpg(name)`

`get_fastpg()` without `name` returns the current context-bound instance.

## Connection manager API

`DBConnectionManager` methods:

- `connect_all()`
- `close_all()`
- `get_db_conn(conn_name)`
- `db_for_read()`
- `db_for_write()`

Validation behavior:

- Raises `ReadConnectionNotAvailableError` if no read connection exists.
- Raises `MultipleWriteConnectionsError` if more than one write connection is configured.
