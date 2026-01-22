# FastPG

FastPG is a lightweight asynchronous ORM for PostgreSQL applications that favour
explicit SQL while still benefiting from Pydantic validation. The project wraps
[`databases`](https://www.encode.io/databases/) with a Django-inspired query API
that fits naturally inside FastAPI services.

## Key features

- **Pydantic-first models** – database rows are hydrated directly into
  subclasses of `DatabaseModel`, allowing you to re-use the same schemas for
  request/response modelling in FastAPI.
- **Async query builder** – chainable `AsyncQuerySet` objects expose familiar
  helpers such as `get`, `filter`, `count`, `update`, `delete`, and
  `get_or_create` while emitting parameterised SQL under the hood.
- **Composable filtering** – the `Q` helper and Django-style lookup suffixes
  provide rich filtering, including nested `OR` conditions, range comparisons,
  JSON updates, and null handling.
- **Relationship loading** – define lightweight relations with `Relation` and
  fetch related rows via `select_related` and `filter_related` in a single round
  trip.
- **Bulk operations and pagination** – insert many rows at once with optional
  conflict handling and page any queryset or raw SQL result using the bundled
  paginator classes.
- **Production niceties** – automatic timestamp management, JSON field helpers,
  configurable logging of SQL execution times, and guard rails around unsafe
  updates and deletes.

## Installation

FastPG requires Python 3.9 or newer.

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

### Configuration

FastPG is configured in Python via `create_fastpg`. You can still read
credentials from environment variables, but you decide how to wire them into
the `databases` mapping.

## Quickstart

Below is a minimal FastAPI application showcasing model declaration,
connection management, and CRUD helpers.

```python
import os
from datetime import datetime
from fastapi import FastAPI
from fastpg import create_fastpg, ConnectionType, DatabaseModel

class Customer(DatabaseModel):
    id: int | None = None
    email: str
    created_at: datetime | None = None

    class Meta:
        db_table = "customers"
        primary_key = "id"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["created_at"]

app = FastAPI()

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
    tz_name="UTC",
)

@app.on_event("startup")
async def connect_db():
    await FAST_PG.db_conn_manager.connect_all()

@app.on_event("shutdown")
async def close_db():
    await FAST_PG.db_conn_manager.close_all()

@app.get("/customers")
async def list_customers():
    return await Customer.async_queryset.all()

@app.post("/customers")
async def create_customer(email: str):
    return await Customer.async_queryset.create(email=email)
```

## Project layout

- `fastpg/` – the core library (models, query builder, pagination, utilities).
- `docs/` – the MkDocs site containing guides and API reference material.
- `mkdocs.yml` – MkDocs configuration, including the navigation tree and theme.

Read on for a deeper dive into models, query construction, pagination, and
advanced patterns. The [settings reference](reference/settings.md) details the
Pythonic configuration options and routing rules for connections.
