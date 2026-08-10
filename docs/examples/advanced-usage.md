# Advanced Usage

These patterns come directly from `test_project/app/api/endpoints/shop_api.py`.

## Load and Filter Multiple Relations

```python
from fastpg import OrderBy

employees = Employee.async_queryset.select_related("department", "location").all()
employees = employees.filter(salary__gte=50000)
employees = employees.filter_related(department__name="Engineering")
employees = employees.filter_related(location__office__icontains="london")
rows = await employees.order_by(salary=OrderBy.DESCENDING)
```

`select_related()` accepts multiple relation names. Each related filter is prefixed by
the relation name used in the model's `Meta.relations` mapping.

## Create Related Rows Atomically

```python
from fastpg import ReturnType, Transaction

async with Transaction.atomic():
    department = await Department.async_queryset.create(name="Engineering")
    location = await Location.async_queryset.create(office="London")
    employee = await Employee.async_queryset.create(
        department_id=department.id,
        location_id=location.id,
        name="Ada",
        email="ada@example.com",
        salary=75000,
        hire_date="2026-08-10",
    )

employee = await (
    Employee.async_queryset
    .select_related("department", "location")
    .get(id=employee.id)
    .return_as(ReturnType.DICT)
)
```

## Prefetch a Filtered Child Collection

```python
from fastpg import Prefetch, ReturnType

employees = Employee.async_queryset.filter(salary__gt=50000)
location = await (
    Location.async_queryset
    .prefetch_related(Prefetch("employees", employees))
    .get(id=1)
    .return_as(ReturnType.DICT)
)
```

The attached `employees` collection contains only rows above the salary threshold.

## Bulk Upsert Order Items

```python
from fastpg import OnConflict

await OrderItem.async_queryset.bulk_create(
    [
        {
            "order_id": order.id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
        }
        for item in order_items
    ],
    on_conflict=OnConflict.UPDATE,
    conflict_target=["order_id", "product_id"],
    update_fields=["quantity", "unit_price"],
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

## `update_or_create`

```python
from fastpg import DuplicateKeyDatabaseError

try:
    product, created = await Product.async_queryset.update_or_create(
        id=1,
        sku="SKU-1",
        defaults={
            "name": "Renamed",
            "price": 12.0,
            "stock_quantity": 100,
            "has_offer": False,
        },
    )
except DuplicateKeyDatabaseError as exc:
    # Translate this to the error response used by your web framework.
    raise ValueError(exc.message) from exc
```

## Arithmetic, JSONB, and Time Updates

```python
await Product.async_queryset.filter(id=1).update(stock_quantity__add=5)
await Product.async_queryset.filter(id=1).update(stock_quantity__sub=2)
await Product.async_queryset.filter(id=1).update(
    properties__jsonb_set__color="blue"
)
await Product.async_queryset.filter(id=1).update(
    properties__jsonb_remove="legacy_key"
)
await Product.async_queryset.filter(
    id=1,
    offer_expires_at__isnull=False,
).update(offer_expires_at__add_time="1 day")
```

`__add_time` and `__sub_time` take a PostgreSQL interval value such as `"1 day"`.

## Nested Order Results

```python
from fastpg import Prefetch

orders = await Order.async_queryset.prefetch_related(
    Prefetch(
        "line_items",
        OrderItem.async_queryset.select_related("product").all(),
    )
).all()
```

## Create or Update a Model Instance

```python
import uuid

coupon, created = await Coupon.async_queryset.get_or_create(
    code="WELCOME",
    defaults={
        "unique_id": uuid.uuid4(),
        "value": 10,
        "value_type": Coupon.CouponTypes.PERCENTAGE,
    },
)

coupon.unique_id = uuid.uuid4()
coupon.value = 250
coupon.value_type = Coupon.CouponTypes.FIXED
coupon.properties["unique_id"] = coupon.unique_id
await coupon.save()
```
