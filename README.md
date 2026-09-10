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

Use Python **3.10 or newer** for this checkout. Package metadata still declares
`>=3.8`, but the current runtime annotations require Python 3.10.

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
- `update()` and `delete()` require base or related filters.
- Unchanged querysets return cached results; modifiers invalidate the cache.

## Documentation

- Getting started: [docs/getting-started.md](docs/getting-started.md)
- Guides: [docs/guides](docs/guides)
- API reference: [docs/api](docs/api)
- Reference: [docs/reference](docs/reference)

## Type hints in VS Code

FastPG ships inline type hints and a `py.typed` marker. Install the Python and
Pylance extensions and select the interpreter where FastPG is installed. No
separate stubs package or editor plugin is required.

Using the `User` model above, Pylance infers these types inside an async function:

```python
from fastpg import AsyncPaginator, ReturnType

user = await User.async_queryset.get(id=1)                    # User
users = await User.async_queryset.filter(name="Ada").limit(5) # list[User]
count = await User.async_queryset.count()                     # int
created = await User.async_queryset.create(name="Ada")        # User
row = await User.async_queryset.get(id=1).return_as(ReturnType.DICT)  # dict[str, Any]
page = await AsyncPaginator(10, User.async_queryset.all()).get_page()
page["results"]  # list[User]; serializer output is inferred when supplied
```

`get()` raises `DoesNotExist` for a missing row, so its result is a model rather
than an optional model. Model fields keep their declared types: an `id: int |
None` remains optional even after fetching or creating a row.

Querysets mutate in place. Keep the returned chain when changing its result
shape (`get`, `filter`, `count`, `update`, `delete`, or `return_as`); type checkers
cannot track those changes through another reference to the same queryset.

Dynamic lookup keywords such as `name__icontains` accept arbitrary values and
are validated at runtime; they do not get model-specific keyword completion.
Relationships attached by `select_related` or `prefetch_related` need explicit
model declarations for attribute completion. Raw SQL/dictionary values and
`JsonData` remain `Any` where their shape is unknown. Pagination `context` can
replace response keys, so supplying it returns a general `dict[str, Any]` type.

For reusable configuration dictionaries, import `DatabaseConfig` and
`QueryLoggerConfig` from `fastpg` to annotate them. `Page[T]` and
`PaginationMetadata` are also exported for pagination response annotations.

To run runtime tests and check the actual wheel in a clean consumer environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python tests/check_typing.py
```

The typing check builds both distribution formats, verifies their marker files,
and runs strict consumer inference checks plus `pyright --verifytypes fastpg
--ignoreexternal` against the installed wheel. Pyright and build tools are only
development dependencies.
