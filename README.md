# FastPG

FastPG is a lightweight asynchronous ORM built on top of [Pydantic](https://docs.pydantic.dev/latest/) and the
[`databases`](https://www.encode.io/databases/) library. It provides a minimal but convenient layer for building
and executing SQL queries in FastAPI projects while keeping explicit SQL within reach.

## Features

- Async query building backed by Pydantic models
- Pagination helpers for query sets and raw SQL
- Configurable preprocessing hooks and logging utilities
- Simple API inspired by Django's ORM

## Installation

FastPG requires Python 3.9 or later. Install directly from GitHub:

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

Or pin it in ``requirements.txt``:

```text
fastpg @ git+https://github.com/bepragma-ai/fastpg.git
```

### Verify the install

```python
from fastpg import __version__

print(__version__)
```

## Configuration

Set the environment variables below (see the [settings reference](https://bepragma-ai.github.io/fastpg/reference/settings/) for details):

- ``FASTPG_TZ`` – timezone used for auto timestamp fields (default: ``UTC``)
- ``POSTGRES_READ_USER`` / ``POSTGRES_WRITE_USER`` – PostgreSQL user for each pool
- ``POSTGRES_READ_PASSWORD`` / ``POSTGRES_WRITE_PASSWORD`` – user password
- ``POSTGRES_READ_DB`` / ``POSTGRES_WRITE_DB`` – database name
- ``POSTGRES_READ_HOST`` / ``POSTGRES_WRITE_HOST`` – database host
- ``POSTGRES_READ_PORT`` / ``POSTGRES_WRITE_PORT`` – database port

## Quickstart

Declare a model and execute a simple query with `AsyncQuerySet`:

```python
from fastpg import DatabaseModel


class User(DatabaseModel):
    id: int
    name: str

    class Meta:
        db_table = "users"


async def list_users():
    return await User.async_queryset.all()
```

The [Getting Started guide](https://bepragma-ai.github.io/fastpg/getting-started/) covers connection management, automatic timestamps, and CRUD helpers. More examples and API details are available throughout the [docs site](https://bepragma-ai.github.io/fastpg/).
