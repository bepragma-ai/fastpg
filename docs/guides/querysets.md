# Querysets

`AsyncQuerySet` offers a fluent interface for building SQL queries. Each chain of
methods produces a lazily evaluated queryset that executes when awaited.

## Core retrieval methods

| Method | Description |
|--------|-------------|
| `get(**kwargs)` | Fetch a single row. Raises `DoesNotExist` or `MultipleRecordsFound` when the result is not unique. |
| `filter(**kwargs)` | Return all rows that match the provided filters. |
| `all()` | Select every row from the table. |
| `count()` | Return the number of rows matching the filters without materialising the result set. |

```python
# Fetch a single customer
from app.schemas.shop import Customer

customer = await Customer.async_queryset.get(id=42)

# Chain filters and ordering
from fastpg import OrderBy

recent = await (
    Customer.async_queryset
    .filter(is_active=True)
    .order_by(created_at=OrderBy.DESCENDING)
    .limit(20)
)
```

Use `columns("id", "email")` to narrow the selected fields, `limit(n)` to
restrict the number of rows, `offset(n)` for pagination, and `order_by(field="ASC")`
to control sorting.

## Lookup expressions

Filters accept Django-style suffixes separated by `__`. A few highlights:

- `field=value` – exact match
- `field__gt=value`, `field__lt=value`, `field__gte=value`, `field__lte=value`
- `field__ne=value` – inequality
- `field__in=[...]` – membership (must be a non-empty list)
- `field__isnull=True/False`
- `field__contains`, `field__icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`

Combine expressions with `Q` objects to build complex `OR` clauses:

```python
from fastpg import Q

adults = Q(age__gte=18)
recent = Q(created_at__gte=window_start)

results = await Customer.async_queryset.filter(adults | recent)
```

## Mutating queries

- `create(**kwargs)` – insert a row and return the new model instance. FastPG
  automatically removes auto-generated fields and populates `auto_now_add`
  fields before writing.
- `bulk_create(values, on_conflict, conflict_target=None, update_fields=None, skip_validations=False)` –
  insert many rows efficiently. Use `OnConflict.DO_NOTHING` to skip duplicate
  rows or `OnConflict.UPDATE` to upsert them.
- `get_or_create(defaults=None, **lookup)` – fetch a row matching the lookup or
  insert a new one using `defaults`.
- `update_or_create(defaults, **lookup)` – update a row with `defaults` when it
  exists, or create it when it does not. Returns a tuple of
  `(instance, created)` where `created` is a boolean.
- `update(**kwargs)` – set or increment fields. Special suffixes include
  `__add`, `__sub`, `__mul`, `__div`, `__jsonb`, `__jsonb_set__path[__type]`,
  `__jsonb_remove` for JSON columns, and `__add_time`/`__sub_time` for
  timestamp arithmetic.
- `delete()` – remove rows that match the current filters.

Both `update` and `delete` require a filter; FastPG raises
`UnrestrictedUpdateError` or `UnrestrictedDeleteError` if you attempt to call
them without a `WHERE` clause.

### Bulk create and upsert

`bulk_create()` is the write-side counterpart to queryset chaining: you hand it
a list of dictionaries and FastPG validates each payload, applies
`auto_now_add` / auto-generated field preprocessing, and sends the batch with
`execute_many()`.

```python
from fastpg import OnConflict

await Product.async_queryset.bulk_create(
    products_batch,
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "category_id", "price", "stock_quantity"],
)
```

The `create_products_in_bulk` endpoint in
`test_project/app/api/endpoints/shop_api.py` uses that pattern to keep the
catalogue in sync by treating `sku` as the unique key.

Use `OnConflict.DO_NOTHING` when duplicates should be ignored rather than
updated:

```python
await OrderItem.async_queryset.bulk_create(
    [
        {
            "order_id": order.id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
        }
        for item in data["order_items"]
    ],
    on_conflict=OnConflict.DO_NOTHING,
)
```

That matches the `create_order` endpoint, which inserts line items inside a
transaction and skips duplicate `(order_id, product_id)` pairs.

When duplicates should overwrite selected columns, pass
`OnConflict.UPDATE` together with both `conflict_target` and `update_fields`:

```python
await OrderItem.async_queryset.bulk_create(
    [
        {
            "order_id": order.id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
        }
        for item in data["order_items"]
    ],
    on_conflict=OnConflict.UPDATE,
    conflict_target=["order_id", "product_id"],
    update_fields=["quantity", "unit_price"],
)
```

That is the same shape used by the `add_order_items` endpoint to upsert order
lines by their composite key.

- `values=[]` raises `NothingToCreateError`.
- Pass `on_conflict=None` explicitly if you want a plain batch insert with no
  conflict clause.
- `skip_validations=True` bypasses Pydantic validation, which is useful for
  trusted pre-validated data paths but removes schema-level safety checks.

### Update suffix examples

Update suffixes let you express common mutations directly in SQL without
round-tripping values through Python. A few practical examples from the shop
demo API:

```python
# Bump inventory without fetching the row first
await Product.async_queryset.filter(id=product_id).update(
    stock_quantity__add=5,
)

# Remove a JSON field while leaving the rest of the document intact
await Product.async_queryset.filter(id=product_id).update(
    properties__jsonb_remove="deprecated_flag",
)

# Extend or shorten a timestamp by a PostgreSQL interval literal
await Product.async_queryset.filter(
    id=product_id,
    offer_expires_at__isnull=False,
).update(
    offer_expires_at__add_time="3 days",   # use __sub_time to shorten
)
```

- `__jsonb_remove` subtracts a key (or path) from a JSON/JSONB column.
- `__add_time` and `__sub_time` apply an interval string (for example, "2 hours"
  or "5 days") to timestamp fields without recalculating them in Python.

### Upsert with `update_or_create`

`update_or_create` is helpful when an API payload might refer to an existing
record by natural keys but you still want a single call to update or insert it.
It combines a lookup, update, and create into one step and returns a tuple of
the resulting model instance and a `created` flag.

```python
product, created = await Product.async_queryset.update_or_create(
    id=payload["id"],
    sku=payload["sku"],
    defaults={
        "name": payload["name"],
        "category_id": payload["category_id"],
        "price": payload["price"],
        "stock_quantity": payload["stock_quantity"],
    },
)

if created:
    log.info("Inserted a new product")
else:
    log.info("Updated existing product %s", product.id)
```

The shop demo endpoint `update_or_create_product` in
`test_project/app/api/endpoints/shop_api.py` uses this pattern when syncing
products.

## Changing the return format

By default, querysets yield model instances. Call
`return_as(ReturnType.MODEL_INSTANCE)` explicitly when you want to ensure nested
relations are hydrated as models, or `return_as(ReturnType.DICT)` to obtain a
list of dictionaries for lightweight serialisation.

```python
from fastpg import ReturnType

raw_rows = await (
    Customer.async_queryset
    .filter(is_active=True)
    .return_as(ReturnType.DICT)
)
```

## Related lookups

When `Meta.relations` is defined, you can fetch related rows in a single
round-trip using `select_related()` and `filter_related()`. For large collections
reach for `prefetch_related()` with a `Prefetch` descriptor.

```python
from fastpg import Prefetch
from app.schemas.shop import OrderItem


orders = await (
    Customer.async_queryset
    .select_related("orders")
    .filter(id=1)
    .filter_related(orders__status="open")
    .prefetch_related(
        Prefetch("line_items", OrderItem.async_queryset.select_related("product").all())
    )
)
```

The related records are hydrated into the attribute named after the relation.
See the [relationships guide](relationships.md) for a detailed example.

## Routing reads

FastPG routes reads to a random read connection by default. To pin a queryset to
a specific connection (for example, a replica), use `using()`:

```python
recent_orders = await Order.async_queryset.using("replica_1").filter(status="open")
```

## Executing custom SQL

For cases where the queryset API is too limiting, use `execute_raw_query()` to
run arbitrary SQL and still benefit from the queryset execution helpers.

```python
rows = await Customer.async_queryset.execute_raw_query(
    "SELECT id, email FROM customers WHERE created_at >= :start",
    {"start": window_start},
)
```

Alternatively, instantiate `AsyncRawQuery` directly for standalone read or write
operations outside of a model context.
