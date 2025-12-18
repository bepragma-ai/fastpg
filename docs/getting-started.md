# Getting started

This guide walks through setting up database connections, defining your first
model, and executing a few queries from a Python REPL or FastAPI application.

## 1. Configure connections

FastPG ships with two `AsyncPostgresDB` connection pools – one for read
operations and one for write operations. Populate the required environment
variables before starting your application:

```bash
export POSTGRES_READ_USER=postgres
export POSTGRES_READ_PASSWORD=secret
export POSTGRES_READ_DB=app
export POSTGRES_READ_HOST=127.0.0.1
export POSTGRES_READ_PORT=5432

export POSTGRES_WRITE_USER=postgres
export POSTGRES_WRITE_PASSWORD=secret
export POSTGRES_WRITE_DB=app
export POSTGRES_WRITE_HOST=127.0.0.1
export POSTGRES_WRITE_PORT=5432

# Optional timezone for auto_now/auto_now_add fields
export FASTPG_TZ=UTC
```

Create the connection pools on startup and close them during shutdown. With
FastAPI you can rely on the event system:

```python
from fastapi import FastAPI
from fastpg.db import ASYNC_DB_READ, ASYNC_DB_WRITE

app = FastAPI()

@app.on_event("startup")
async def connect_db():
    await ASYNC_DB_READ.connect()
    await ASYNC_DB_WRITE.connect()

@app.on_event("shutdown")
async def close_db():
    await ASYNC_DB_READ.close()
    await ASYNC_DB_WRITE.close()
```

For scripts or tests you can manage the lifecycle manually:

```python
import asyncio
from fastpg.db import ASYNC_DB_READ, ASYNC_DB_WRITE

async def bootstrap():
    await ASYNC_DB_READ.connect()
    await ASYNC_DB_WRITE.connect()

asyncio.run(bootstrap())
```

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
`auto_now*` fields using the timezone chosen in `FASTPG_TZ`.

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
