# Advanced Usage

These patterns come directly from `test_project/app/api/endpoints/shop_api.py`.

## Select Related With Related Filtering

```python
from fastpg import OrderBy

employees = Employee.async_queryset.select_related("department")
employees = employees.filter(salary__gte=50000)
employees = employees.filter_related(department__name="Engineering")
rows = await employees.order_by(salary=OrderBy.DESCENDING)
```

## Prefetch Child Collections

```python
from fastpg import Prefetch, ReturnType

rows = await (
    Department.async_queryset
    .prefetch_related(Prefetch("employees", Employee.async_queryset.all()))
    .all()
    .return_as(ReturnType.DICT)
)
```

## Raw SQL With `IN` Parameters

```python
from fastpg import AsyncRawQuery, InClauseParam

rows = await AsyncRawQuery(
    query="""
        SELECT * FROM orders
        WHERE id IN (:order_ids)
          AND customer_id IN (:customer_ids)
          AND total_amount >= :total_amount
    """
).fetch(
    values={
        "order_ids": InClauseParam([1, 2, 3]),
        "customer_ids": InClauseParam([10, 11]),
        "total_amount": 100,
    }
)
```

## Transaction Pattern

```python
from fastpg import Transaction


async def create_department_with_employees(dept, employees):
    async with Transaction.atomic():
        department = await Department.async_queryset.create(**dept)
        for emp in employees:
            emp["department_id"] = department.id
            await Employee.async_queryset.create(**emp)
    return department
```

## `update_or_create`

```python
product, created = await Product.async_queryset.update_or_create(
    id=1,
    sku="SKU-1",
    defaults={"name": "Renamed", "price": 12.0, "stock_quantity": 100},
)
```

## Queryset Pagination

```python
from fastpg import AsyncPaginator

paginator = AsyncPaginator(
    page_size=20,
    queryset=Product.async_queryset.all(),
)

page = await paginator.get_page(1)
```
