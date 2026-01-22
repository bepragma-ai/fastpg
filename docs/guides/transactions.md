# Transactions

FastPG exposes the underlying [`databases`](https://www.encode.io/databases/connection_pooling/#transactions)
transaction helpers through the active FastPG instance. Each transaction is
bound to the connection used by the current async task, so long-lived tasks
should acquire and release them carefully.

## Prerequisites

Ensure the FastPG instance is connected before opening a transaction:

```python
from fastpg import Transaction

# elsewhere during startup:
# await FAST_PG.db_conn_manager.connect_all()
```

Transactions are always backed by the write connection.

## Context manager (recommended)

Wrap related operations in an `async with` block. The transaction is committed
when the block exits normally and rolled back if an exception is raised.

```python
async def create_users(payload: list[dict]):
    async with Transaction.atomic():
        for data in payload:
            await User.async_queryset.create(**data)
```

## Manual control

When you need explicit control over commit/rollback, grab the transaction
instance and manage it yourself:

```python
transaction = await Transaction.start()
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
@Transaction.decorator()
async def create_users(request):
    ...
```

This pattern is useful for FastAPI dependencies or background tasks where the
function body should always execute inside a transaction.
