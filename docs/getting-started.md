# Getting Started

## 1. Install

From a local checkout:

```bash
pip install -e .
```

From GitHub:

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

FastPG targets Python `>=3.8`.

## 2. Configure FastPG

Create one FastPG instance during app startup:

```python
import os
from fastapi import FastAPI
from fastpg import ConnectionType, create_fastpg

app = FastAPI()

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

- At least one `ConnectionType.READ` connection is required.
- Exactly one `ConnectionType.WRITE` connection is expected.
- Reads go through a randomly chosen read connection.
- Writes always use the configured write connection.

If you register more than one FastPG instance, switch the active one with `set_current_fastpg(name)`.

## 3. Open and Close Connections

```python
@app.on_event("startup")
async def on_startup():
    await FAST_PG.db_conn_manager.connect_all()


@app.on_event("shutdown")
async def on_shutdown():
    await FAST_PG.db_conn_manager.close_all()
```

## 4. Define a Model

```python
from datetime import datetime
from fastpg import DatabaseModel


class Customer(DatabaseModel):
    id: int | None = None
    name: str
    email: str
    created_at: datetime | None = None

    class Meta:
        db_table = "customers"
        primary_key = "id"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["created_at"]
```

## 5. Run CRUD Queries

```python
# Create
new_customer = await Customer.async_queryset.create(
    name="Ada",
    email="ada@example.com",
)

# Read one
customer = await Customer.async_queryset.get(id=new_customer.id)

# Read many
customers = await Customer.async_queryset.filter(name__icontains="ada")

# Update rows
updated = await Customer.async_queryset.filter(id=customer.id).update(
    name="Ada Lovelace",
)

# Delete rows
deleted = await Customer.async_queryset.filter(id=customer.id).delete()
```

## 6. Use Instance Helpers

```python
customer = await Customer.async_queryset.get(id=1)
customer.name = "Updated Name"
await customer.save(columns=["name"])
await customer.delete()
```

## 7. Drop to Raw SQL

```python
from fastpg import AsyncRawQuery

records = await AsyncRawQuery(
    query="SELECT id, email FROM customers WHERE id > :min_id"
).fetch(values={"min_id": 10})
```
