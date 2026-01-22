# Getting started

This guide walks through setting up database connections, defining your first
model, and executing a few queries from a Python REPL or FastAPI application.

## 1. Configure connections

FastPG uses a Python-first configuration API. Create a FastPG instance with a
read connection (or replicas) and a single write connection:

```python
import os
from fastapi import FastAPI
from fastpg import create_fastpg, ConnectionType

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
```

Connect on startup and close on shutdown:

```python
@app.on_event("startup")
async def connect_db():
    await FAST_PG.db_conn_manager.connect_all()

@app.on_event("shutdown")
async def close_db():
    await FAST_PG.db_conn_manager.close_all()
```

For scripts or tests you can manage the lifecycle manually:

```python
import asyncio

async def bootstrap():
    await FAST_PG.db_conn_manager.connect_all()

asyncio.run(bootstrap())
```

FastPG routes reads to a random read connection and writes to the single write
connection. To target a specific connection for a read, use
`Customer.async_queryset.using("replica_1")`.

## 2. Declare models

Models inherit from `DatabaseModel` (a `pydantic.BaseModel` subclass). Define a
nested `Meta` class to configure the backing table, primary key, automatic
fields, and optional relationships.

```python
from datetime import datetime
from fastpg import DatabaseModel

class Customer(DatabaseModel):
    id: int | None = None
    email: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Meta:
        db_table = "customers"
        primary_key = "id"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["created_at"]
        auto_now_fields = ["updated_at"]
```

When you call `create` or `save`, FastPG will automatically populate the
`auto_now*` fields using the timezone chosen in `tz_name`.

## 3. Run queries

Interact with the asynchronous queryset using familiar ORM-style helpers.

```python
# Insert a row and capture the returned model instance
customer = await Customer.async_queryset.create(email="ada@example.com")

# Fetch rows
first = await Customer.async_queryset.get(id=customer.id)
active = await Customer.async_queryset.filter(is_active=True)
count = await Customer.async_queryset.count()

# Update and delete
await Customer.async_queryset.filter(id=customer.id).update(is_active=False)
await Customer.async_queryset.filter(id=customer.id).delete()
```

In unit tests you can use `pytest.mark.anyio` or `pytest-asyncio` to run the
coroutines. The models behave like regular Pydantic models, so you can call
`.model_dump()` to serialise responses or feed them directly into FastAPI route
responses.

## Next steps

Read the concept guides for detailed explanations of metadata, filtering,
relations, and pagination, or jump straight to the API reference for a
method-by-method breakdown. Connection settings are covered in
[Settings & Logging](reference/settings.md).
