# Transactions

FastPG exposes transaction helpers through `Transaction`.

## Context manager (recommended)

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

## Manual flow

```python
transaction = await Transaction.start()
try:
    await Order.async_queryset.create(customer_id=1, total_amount=99.5, status="PENDING", order_date="2025-01-01")
except Exception:
    await transaction.rollback()
    raise
else:
    await transaction.commit()
```

## Decorator style

```python
from fastpg import Transaction


@Transaction.decorator()
async def create_coupon(payload):
    return await Coupon.async_queryset.create(**payload)
```

## Notes

- Transactions use the configured write connection.
- Open connections first (`connect_all()`) before starting transactions.
