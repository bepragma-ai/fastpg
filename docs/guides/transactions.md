# Transactions

Transactions are managed by async context blocks. Transaction state is tied to the connection used in the currently executing asynchronous task.

## Acquiring transactions

A transaction can be acquired from the database connection pool:

```python
from fastpg.db import ASYNC_DB_WRITE


async with ASYNC_DB_WRITE.transaction():
    ...
```

## Implementing transactions

A transaction can be implemented in any of the following ways

```python
from fastpg.db import ASYNC_DB_WRITE


async with ASYNC_DB_WRITE.transaction():
    ...
```

For a lower-level transaction API:

```python
transaction = await ASYNC_DB_WRITE.transaction()
try:
    ...
except:
    await transaction.rollback()
else:
    await transaction.commit()
```

You can also use .transaction() as a function decorator on any async function:

```python
@ASYNC_DB_WRITE.transaction()
async def create_users(request):
    ...
```