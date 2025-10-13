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

### Environment variables

Provide PostgreSQL credentials and optional timezone configuration through the
following variables:

- `FASTPG_TZ` – timezone used for auto timestamp fields (defaults to `UTC`).
- `POSTGRES_READ_*` and `POSTGRES_WRITE_*` – credentials used by the read and
  write connection pools respectively.

## Quickstart

Below is a minimal FastAPI application showcasing model declaration,
connection management, and CRUD helpers.

```python
from fastapi import FastAPI
from fastpg import DatabaseModel, ASYNC_DB_READ, ASYNC_DB_WRITE

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

@app.on_event("startup")
async def connect_db():
    await ASYNC_DB_READ.connect()
    await ASYNC_DB_WRITE.connect()

@app.on_event("shutdown")
async def close_db():
    await ASYNC_DB_READ.close()
    await ASYNC_DB_WRITE.close()

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
advanced patterns.
