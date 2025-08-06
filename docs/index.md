# FastPG

FastPG is a lightweight ORM for FastAPI projects backed by PostgreSQL. It leverages Pydantic models and async database drivers to keep applications fast and easy to maintain.

# Installation

FastPG supports Python 3.9 and newer.

## Using pip

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

## Environment variables

Set the following optional variables to configure FastPG:

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

## Verify installation

```bash
python -c "import fastpg; print(fastpg.__version__)"
```

# Quickstart

This quickstart demonstrates defining a model, creating the database tables,
performing CRUD operations, and paginating results.

```python
from fastpg import DatabaseModel, ASYNC_CUSTOMERS_DB_WRITE

class Item(DatabaseModel):
    id: int
    name: str

    class Meta:
        db_table = "items"

async def main():
    # Create a record
    await ASYNC_CUSTOMERS_DB_WRITE.execute(
        "INSERT INTO items(id, name) VALUES (:id, :name)",
        {"id": 1, "name": "Widget"},
    )

    # Query records
    results = await Item.async_queryset.all()
    print(results)
```
