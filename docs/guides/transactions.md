# Transactions

FastPG exposes the underlying [`databases`](https://www.encode.io/databases/connection_pooling/#transactions)
transaction helpers through the `AsyncPostgresDB` instances in `fastpg.db`.
Each transaction is bound to the connection used by the current async task, so
long-lived tasks should acquire and release them carefully.

## Prerequisites

Import the connection pools from `fastpg.db` and ensure they are connected
before opening a transaction:

```python
from fastpg.db import ASYNC_DB_WRITE

# elsewhere during startup:
# await ASYNC_DB_WRITE.connect()
```

Use `ASYNC_DB_WRITE` for write operations. `ASYNC_DB_READ` supports the same
API but should only be used for read-only transactions.

## Context manager (recommended)

Wrap related operations in an `async with` block. The transaction is committed
when the block exits normally and rolled back if an exception is raised.

```python
async def create_users(payload: list[dict]):
    async with ASYNC_DB_WRITE.transaction():
        for data in payload:
            await User.async_queryset.create(**data)
```

## Manual control

When you need explicit control over commit/rollback, grab the transaction
instance and manage it yourself:

```python
transaction = await ASYNC_DB_WRITE.transaction()
try:
    await User.async_queryset.create(**user_data)
    await AuditLog.async_queryset.create(event="user.created")
except Exception:
    await transaction.rollback()
    raise
else:
    await transaction.commit()
```

## Decorator style

Transactions can also wrap async callables using decorator syntax:

```python
@ASYNC_DB_WRITE.transaction()
async def create_users(request):
    ...
```

This pattern is useful for FastAPI dependencies or background tasks where the
function body should always execute inside a transaction.
