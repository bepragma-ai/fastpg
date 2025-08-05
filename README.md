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
- ``POSTGRES_READ_*`` / ``POSTGRES_WRITE_*`` – credentials for read and write
  database connections

## Quick Example

```python
from fastpg import DatabaseModel

class User(DatabaseModel):
    id: int
    name: str

    class Meta:
        db_table = "users"


async def list_users():
    return await User.objects.all().fetch()
```

More examples and API documentation are available in the [docs](docs/).

