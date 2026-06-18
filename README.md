# FastPG

FastPG is a lightweight async ORM layer for PostgreSQL applications, especially FastAPI services. It combines `pydantic` models with the `databases` package and keeps the generated SQL simple and explicit.

## Features

- Pydantic-backed database models with async CRUD helpers
- Lazy `AsyncQuerySet` API with Django-style lookup suffixes
- Explicit relationship loading with `select_related` and `prefetch_related`
- Bulk inserts with PostgreSQL conflict handling
- Raw SQL support with FastPG error wrapping
- Built-in paginators and transaction helpers

## Installation

FastPG requires Python `>=3.8`.

From a local checkout:

```bash
pip install -e .
```

From GitHub:

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

Or pin it in `requirements.txt`:

```text
fastpg @ git+https://github.com/bepragma-ai/fastpg.git
```

## Configuration

FastPG does not read environment variables on its own. Your application should build the database config and register a FastPG instance explicitly:

```python
import os
from fastpg import ConnectionType, create_fastpg


FAST_PG = create_fastpg(
    name="api",
    databases={
        "default": {
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
    tz_name="UTC",
    query_logger={
        "LOG_QUERIES": True,
        "TITLE": "MY_SERVICE",
    },
)
```

Connection rules:

- At least one `READ` connection is required.
- Exactly one `WRITE` connection should be configured.
- Reads are routed to a random read connection.
- Writes always use the write connection.

Open and close connections with `FAST_PG.db_conn_manager.connect_all()` and `close_all()` during app startup and shutdown.

## Quickstart

```python
from fastpg import DatabaseModel


class User(DatabaseModel):
    id: int | None = None
    name: str

    class Meta:
        db_table = "users"
        primary_key = "id"
        auto_generated_fields = ["id"]


async def create_and_list_users():
    user = await User.async_queryset.create(name="Ada")
    rows = await User.async_queryset.all()
    return user, rows
```

Important implementation notes:

- `create()` performs a plain `INSERT ... RETURNING`.
- `bulk_create()` is where `OnConflict.DO_NOTHING` and `OnConflict.UPDATE` apply.
- `update()` and `delete()` should be chained after `filter(...)`.

## Documentation

- Getting started: [docs/getting-started.md](docs/getting-started.md)
- Guides: [docs/guides](docs/guides)
- API reference: [docs/api](docs/api)
- Reference: [docs/reference](docs/reference)
