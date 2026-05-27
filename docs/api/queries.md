# Query API

The query API comprises `AsyncQuerySet` for model-bound operations and
`AsyncRawQuery` for ad-hoc SQL.

## AsyncQuerySet

### Creation helpers

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

| Method | Purpose |
|--------|---------|
| `get(**filters)` | Fetch a single row. |
| `filter(*conditions, **filters)` | Fetch multiple rows using keyword lookups or `Q` objects. |
| `all()` | Return every row. |
| `count()` | Return the number of matching rows. |
| `columns(*names)` | Select a subset of columns. |
| `order_by(**clauses)` | Accepts a mapping of column → `"ASC"`/`"DESC"`. |
| `limit(n)` / `offset(n)` | Apply pagination clauses. |
| `return_as(ReturnType)` | Switch between model instances and dictionaries. |
| `select_related(*relation_names)` | Join related tables defined in `Meta.relations`. |
| `filter_related(*conditions, **filters)` | Apply filters to the joined tables. |

### Mutation helpers

| Method | Purpose |
|--------|---------|
| `update(**values)` | Update rows matching the current filters. Supports arithmetic (`__add`, `__sub`, `__mul`, `__div`), JSON (`__jsonb`, `__jsonb_set__path`, `__jsonb_remove`), and interval (`__add_time`, `__sub_time`) suffixes. |
| `delete()` | Delete rows matching the filters. |

Awaiting a queryset triggers execution. If no terminal method has been called,
`MalformedQuerysetError` is raised.

## AsyncRawQuery

`AsyncRawQuery` wraps raw SQL statements while still providing consistent error
handling.

| Method | Purpose |
|--------|---------|
| `fetch(values)` | Execute a SELECT-like statement and return dictionaries. |
| `execute(values)` | Execute a modifying statement. |
| `execute_many(list_of_values)` | Execute the same statement with multiple sets of parameters. |

Use raw queries when you need window functions, CTEs, or other constructs that
are easier to express directly in SQL.
