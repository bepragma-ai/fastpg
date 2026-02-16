# Getting Started

## 1. Install

FastPG is currently installed from GitHub:

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

## 2. Configure FastPG

Create one FastPG instance at app startup.

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
    query_logger={
        "LOG_QUERIES": True,
        "TITLE": "MY_SERVICE",
    },
)
```

Connection rules:

- At least one `ConnectionType.READ` connection is required.
- Only one `ConnectionType.WRITE` connection should be configured.
- Reads route to a random read connection.
- Writes always route to the write connection.

## 3. Connect and close pools

```python
@app.on_event("startup")
async def on_startup():
    await FAST_PG.db_conn_manager.connect_all()


@app.on_event("shutdown")
async def on_shutdown():
    await FAST_PG.db_conn_manager.close_all()
```

## 4. Define your first model

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

## 5. Run CRUD queries

```python
# Create
new_customer = await Customer.async_queryset.create(name="Ada", email="ada@example.com")

# Read one
customer = await Customer.async_queryset.get(id=new_customer.id)

# Read many
customers = await Customer.async_queryset.filter(name__icontains="a")

# Update rows (always filter first)
updated = await Customer.async_queryset.filter(id=customer.id).update(name="Ada Lovelace")

# Delete rows (always filter first)
deleted = await Customer.async_queryset.filter(id=customer.id).delete()
```

## 6. Use model instance helpers

```python
customer = await Customer.async_queryset.get(id=1)
customer.name = "Updated Name"
await customer.save(columns=["name"])
await customer.delete()
```

## 7. Use raw SQL when needed

```python
from fastpg import AsyncRawQuery

records = await AsyncRawQuery(
    query="SELECT id, email FROM customers WHERE id > :min_id"
).fetch(values={"min_id": 10})
```
