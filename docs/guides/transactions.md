# Transactions

FastPG exposes write-side transaction helpers through `Transaction`.

## Context Manager

```python
from fastpg import Transaction


async def create_department_and_employees(dept_data, employees_data):
    async with Transaction.atomic():
        department = await Department.async_queryset.create(**dept_data)
        for emp in employees_data:
            emp["department_id"] = department.id
            await Employee.async_queryset.create(**emp)
    return department
```

This is the safest pattern and matches the sample FastAPI project.

## Manual Flow

```python
transaction = await Transaction.start()
try:
    await Order.async_queryset.create(
        customer_id=1,
        order_date="2025-01-01",
        total_amount=99.5,
        status="PENDING",
    )
except Exception:
    await transaction.rollback()
    raise
else:
    await transaction.commit()
```

## Decorator Style

```python
from fastpg import Transaction


@Transaction.decorator()
async def create_coupon(payload):
    return await Coupon.async_queryset.create(**payload)
```

## Notes

- Transactions are taken from the configured write connection.
- Call `connect_all()` before using transaction helpers.
- `Transaction.atomic()` returns the underlying transaction context manager.
