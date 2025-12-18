# Advanced usage

This example mirrors the `shop` API used in the test project and shows multiple
features working together: joined queries, [prefetching](../guides/relationships.md#prefetching-child-collections),
conflict-aware bulk writes, and multiple return types that plug straight into
FastAPI responses.

```python
from datetime import date
from fastpg import (
    DatabaseModel,
    Relation,
    Prefetch,
    ReturnType,
    OnConflict,
    OrderBy,
)


class Customer(DatabaseModel):
    id: int | None = None
    name: str
    email: str
    city: str

    class Meta:
        db_table = "customers"
        auto_generated_fields = ["id"]


class Product(DatabaseModel):
    id: int | None = None
    sku: str
    name: str
    price: float

    class Meta:
        db_table = "products"
        auto_generated_fields = ["id"]


class OrderItem(DatabaseModel):
    id: int | None = None
    order_id: int
    product_id: int
    quantity: int
    unit_price: float

    class Meta:
        db_table = "order_items"
        auto_generated_fields = ["id"]
        relations = {
            "product": Relation(Product, base_field="product_id", foreign_field="id"),
        }


class Order(DatabaseModel):
    id: int | None = None
    customer_id: int
    order_date: date
    total_amount: float
    status: str

    class Meta:
        db_table = "orders"
        auto_generated_fields = ["id"]
        relations = {
            "customer": Relation(Customer, base_field="customer_id", foreign_field="id"),
            "line_items": Relation(
                OrderItem,
                base_field="id",
                foreign_field="order_id",
                related_data_set_name="line_items",
            ),
        }


# Shared department lookup used across employee endpoints
class Department(DatabaseModel):
    id: int | None = None
    name: str
    location: str

    class Meta:
        db_table = "departments"
        auto_generated_fields = ["id"]


class Employee(DatabaseModel):
    id: int | None = None
    department_id: int | None
    name: str
    email: str
    salary: float

    class Meta:
        db_table = "employees"
        auto_generated_fields = ["id"]
        relations = {
            "department": Relation(Department, base_field="department_id", foreign_field="id"),
        }


# 1. Bulk upsert a batch of products for catalogue maintenance
await Product.async_queryset.bulk_create(
    [
        {"sku": "SKU-100", "name": "Noise Cancelling Headphones", "price": 249.0},
        {"sku": "SKU-101", "name": "Wireless Mouse", "price": 39.0},
    ],
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "price"],
)


# 2. Serve employees with joined department data for a dashboard
employees = await Employee.async_queryset.select_related("department").order_by(
    salary=OrderBy.DESCENDING
)


# 3. Build a nested order payload using select_related and prefetch_related
orders = await (
    Order.async_queryset
    .select_related("customer")
    .prefetch_related(
        Prefetch(
            "line_items",
            OrderItem.async_queryset.select_related("product").all(),
        )
    )
    .filter(status="processing")
)


# 4. Serialise the same query as dictionaries when JSON is preferred
orders_payload = await (
    Order.async_queryset
    .prefetch_related(
        Prefetch(
            "line_items",
            OrderItem.async_queryset.select_related("product").all(),
        )
    )
    .filter(status="processing")
    .return_as(ReturnType.DICT)
)
```

The resulting structures can be returned directly from FastAPI endpoints, just
like the demo routes in `test_project/app/api/endpoints/shop_api.py`. Bulk
operations keep product data fresh, `select_related` joins customer details to an
order, and `prefetch_related` assembles a rich response for nested collections
without hand-written SQL. Learn more in the [relationships guide](../guides/relationships.md).

## Managing transactions for multi-step writes

When a write spans multiple tables, wrap it in a database transaction so either
all steps succeed or none do. The shop demo exposes this flow through the
`create_department_with_employees` endpoint, which uses `ASYNC_DB_WRITE` to
wrap department creation and employee inserts in a single unit of work. See the
[transactions guide](../guides/transactions.md) for the full API.

```python
from fastpg.db import ASYNC_DB_WRITE


async def create_department_with_employees(department_data, employees_data):
    async with ASYNC_DB_WRITE.transaction():
        department = await Department.async_queryset.create(**department_data)
        for emp in employees_data:
            emp["department_id"] = department.id
            await Employee.async_queryset.create(**emp)
    return department
```

`ASYNC_DB_WRITE.transaction()` supports async context managers, decorators, or
manual begin/commit calls. In every mode, FastPG will roll back the transaction
if an exception is raised so partial writes never hit the database.
