# Transactions

FastPG exposes write-side transaction helpers through `Transaction`.

Examples use the configured test-project models. Open connections before running
them, or use `bash docker.sh shell` from `test_project/`.

## Context Manager

```python
from fastpg import Transaction
from app.schemas.shop import Department, Employee


async def create_department_and_employees(dept_data, employees_data):
    async with Transaction.atomic():
        department = await Department.async_queryset.create(**dept_data)
        for emp in employees_data:
            await Employee.async_queryset.create(**{**emp, "department_id": department.id})
    return department
```

Successful exit commits the transaction; an exception rolls it back.

## Manual Flow

```python
from fastpg import Transaction
from app.schemas.shop import Order

transaction = await Transaction.start()
try:
    await Order.async_queryset.create(
        customer_id=1,
        order_date="2025-01-01",
        total_amount=99.5,
        status="PENDING",
    )
except BaseException:
    await transaction.rollback()
    raise
else:
    await transaction.commit()
```

## Decorator Style

```python
from fastpg import Transaction
from app.schemas.shop import Coupon


@Transaction.decorator()
async def create_coupon(payload):
    return await Coupon.async_queryset.create(**payload)
```

## Notes

- Transactions are taken from the configured write connection.
- Call `connect_all()` before using transaction helpers.
- `Transaction.atomic()` returns the underlying transaction context manager.
- Normal reads still use a read connection, even inside `Transaction.atomic()`.
  Use `.using("default")` with the example configuration to read from the write
  connection and see uncommitted changes made in that transaction.
- Keep the active FastPG instance consistent with the objects being written;
  existing objects retain their originating connection when the active instance changes.

## Row Locks

`lock_for_update()` must be awaited inside the transaction that needs the lock.
It uses the write connection automatically and returns a list:

```python
from fastpg import Transaction
from app.schemas.shop import Product

async with Transaction.atomic():
    products = await Product.async_queryset.filter(id=1).lock_for_update()
    if not products:
        raise ValueError("Product not found")
    products[0].stock_quantity += 1
    await products[0].save(columns=["stock_quantity"])
```

Current constraints:

- Use `filter(...)`, including when matching one primary key; `get()` is not supported.
- `select_related()` is supported and preserves related filters. Only the base
  rows are locked (`FOR UPDATE OF t`), not the joined rows.
- Prefetching, ordering, limits, and offsets are rejected with `MalformedQuerysetError`.
- Locks end when the transaction commits or rolls back. Outside an explicit
  transaction, the lock ends with the statement and cannot protect a later write.
- Construct a fresh locking queryset for each transaction; an unchanged queryset
  can otherwise return a previously cached result without acquiring a new lock.

## Verify Lock Contention

Paste this into the test-project shell. Supply an existing employee ID. It does
not change row data: the second transaction must time out while the first holds
the lock, then succeed after the first transaction finishes.

```python
import asyncio
from fastpg import Transaction, get_fastpg
from fastpg.errors import DatabaseError
from app.schemas.shop import Employee


async def test_lock(employee_id):
    write = get_fastpg().db_conn_manager.db_for_write()

    async def contender():
        async with Transaction.atomic():
            await write.execute(query="SET LOCAL lock_timeout = '500ms'")
            rows = await Employee.async_queryset.filter(id=employee_id).lock_for_update()
            assert len(rows) == 1, "Use an existing employee ID"

    async with Transaction.atomic():
        rows = await Employee.async_queryset.filter(id=employee_id).lock_for_update()
        assert len(rows) == 1, "Use an existing employee ID"
        try:
            # A separate task uses a separate connection for the competing transaction.
            await asyncio.wait_for(asyncio.create_task(contender()), timeout=3)
        except DatabaseError as exc:
            assert exc.sqlstate == "55P03", str(exc)
            print("PASS: second transaction was blocked")
        else:
            raise AssertionError("Expected lock contention")

    await contender()
    print("PASS: lock released after transaction ended")


await test_lock(1)  # Replace with an existing employee ID.
```
