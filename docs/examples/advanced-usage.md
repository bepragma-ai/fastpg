# Advanced Usage

Examples below come directly from `test_project/app/api/endpoints/shop_api.py` patterns.

## Select related + related filtering

```python
from fastpg import OrderBy

employees = Employee.async_queryset.select_related("department").all()
employees = employees.filter(salary__gte=50000)
employees = employees.filter_related(department__name="Engineering")
rows = await employees.order_by(salary=OrderBy.DESCENDING)
```

## Prefetch child collections

```python
from fastpg import Prefetch, ReturnType

rows = await (
    Department.async_queryset
    .prefetch_related(Prefetch("employees", Employee.async_queryset.all()))
    .all()
    .return_as(ReturnType.DICT)
)
```

## Transaction patterns

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

## Update-or-create

```python
product, created = await Product.async_queryset.update_or_create(
    id=1,
    sku="SKU-1",
    defaults={"name": "Renamed", "price": 12.0, "stock_quantity": 100},
)
```

## Queryset pagination for API responses

```python
from fastpg import AsyncPaginator

paginator = AsyncPaginator(
    page_size=20,
    queryset=Product.async_queryset.all(),
)

page = await paginator.get_page(1)
return page
```
