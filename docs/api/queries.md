# Query API

## `AsyncQuerySet(model)`

Main query builder for model operations.

### Core methods

<<<<<<< HEAD
- `using(conn_name)`
- `columns(*columns)`
- `get(*conditions, **filters)`
- `filter(*conditions, **filters)`
- `all()`
- `count()`
- `order_by(**order_by)`
- `limit(fetch_limit)`
- `offset(fetch_offset)`
- `return_as(return_type)`

### Relationship methods
=======
| Method | Purpose |
|--------|---------|
| `create(**kwargs)` | Insert a single row and return the model instance. |
| `bulk_create(values, on_conflict, conflict_target=None, update_fields=None, skip_validations=False)` | Batch insert. Pass `OnConflict.DO_NOTHING` to ignore duplicates or `OnConflict.UPDATE` to upsert matching rows. |
| `get_or_create(defaults=None, **lookup)` | Return an existing row or create one from `defaults`. |

#### `bulk_create`

`bulk_create()` accepts a list of dictionaries and writes them with a single
statement template executed through `execute_many()`.

- `values` must be a non-empty `list[dict]`. An empty list raises `NothingToCreateError`.
- `on_conflict` controls whether FastPG emits an `ON CONFLICT` clause. Pass
  `None` explicitly for a plain batch insert, `OnConflict.DO_NOTHING` to ignore
  duplicates, or `OnConflict.UPDATE` to perform an upsert.
- `conflict_target` and `update_fields` are required when
  `on_conflict=OnConflict.UPDATE`.
- `skip_validations=True` bypasses Pydantic validation with
  `model_construct()`, but FastPG still fills `auto_now_add` and
  auto-generated fields before writing.

```python
from fastpg import OnConflict

# Plain batch insert
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
    on_conflict=None,
)

# Ignore duplicates when an order item already exists
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

# Upsert products by SKU, matching the shop demo API
await Product.async_queryset.bulk_create(
    products_batch,
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "category_id", "price", "stock_quantity"],
)
```

### Retrieval helpers
>>>>>>> origin/main

- `select_related(*relation_names)`
- `filter_related(*conditions, **filters)`
- `prefetch_related(*prefetches)`

### Mutation methods

- `create(on_conflict=None, conflict_target=None, update_fields=None, **kwargs)`
- `bulk_create(values, skip_validations=False, on_conflict=None, conflict_target=None, update_fields=None)`
- `get_or_create(defaults, **kwargs)`
- `update_or_create(defaults, **kwargs)`
- `update(**kwargs)`
- `delete()`

### Await behavior

Awaiting queryset executes SQL and returns based on action:

- `get()` -> one model/dict, or raises cardinality errors.
- `filter()` / `all()` -> list.
- `count()` -> integer.
- `update()` / `delete()` -> affected row count from write query.

## `AsyncRawQuery(query, using=None)`

Raw SQL wrapper with FastPG error handling.

### Methods

- `fetch(values)` -> list of dict records (read connection)
- `execute(values)` -> execute single write query
- `execute_many(list_of_values)` -> execute write query with many parameter sets

## `AsyncPaginator(page_size, queryset, using=None)`

Paginates an `AsyncQuerySet` and returns `results` plus `results_paginator` metadata.

## `RawQueryAsyncPaginator(...)`

Paginates raw SQL with optional serializer and auto `LIMIT/OFFSET` handling.
