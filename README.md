# FastPG

FastPG is a lightweight asynchronous ORM built on top of Pydantic and the
``databases`` library. It provides a minimal but convenient layer for building
and executing SQL queries in FastAPI projects.

## Features

- Async query building with Pydantic models
- Pagination helpers for query sets and raw SQL
- Configurable preprocessing hooks and logging utilities
- Simple API inspired by Django's ORM

## Installation

FastPG requires Python 3.9 or later. Install directly from GitHub:

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

In ``requirements.txt``:

```text
fastpg @ git+https://github.com/bepragma-ai/fastpg.git
```

Optional environment variables:

- ``FASTPG_TZ`` – timezone used for auto timestamp fields (default: ``UTC``)
- ``POSTGRES_READ_USER`` - Postgresql read DB user
- ``POSTGRES_READ_PASSWORD`` - Postgresql read DB password
- ``POSTGRES_READ_DB`` - Postgresql read DB name
- ``POSTGRES_READ_HOST`` - Postgresql read DB host
- ``POSTGRES_READ_PORT`` - Postgresql read DB port
- ``POSTGRES_WRITE_USER`` - Postgresql write DB user
- ``POSTGRES_WRITE_PASSWORD`` - Postgresql write DB password
- ``POSTGRES_WRITE_DB`` - Postgresql write DB name
- ``POSTGRES_WRITE_HOST`` - Postgresql write DB host
- ``POSTGRES_WRITE_PORT`` - Postgresql write DB port

## Quick Example

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

More examples and API documentation are available in the [docs](https://bepragma-ai.github.io/fastpg/).
