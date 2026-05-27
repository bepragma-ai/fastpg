# Querysets

`AsyncQuerySet` builds SQL lazily and executes when awaited.

## Execution model

A queryset must end in one of these actions before awaiting:

- `get(...)`
- `filter(...)`
- `all()`
- `count()`
- `update(...)`
- `delete()`

Otherwise, awaiting raises `MalformedQuerysetError`.

## Read methods

```python
user = await User.async_queryset.get(id=1)
users = await User.async_queryset.filter(name__icontains="ada")
all_users = await User.async_queryset.all()
total = await User.async_queryset.filter(is_active=True).count()
```

`get(...)` and `filter(...)` should be called with at least one condition (`Q(...)` or keyword filters).

## Lookup operators

Supported filter suffixes:

- `__gt`, `__lt`, `__gte`, `__lte`, `__ne`
- `__in` (requires a non-empty list)
- `__isnull`
- `__contains`, `__icontains`
- `__startswith`, `__istartswith`
- `__endswith`, `__iendswith`

## Combining filters with `Q`

```python
from fastpg import Q

q = Q(city="Boston") | Q(city="New York")
results = await Customer.async_queryset.filter(q, is_active=True)
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
from fastpg import OrderBy, ReturnType

rows = await (
    Product.async_queryset
    .columns("id", "name", "price")
    .filter(price__gte=100)
    .order_by(price=OrderBy.DESCENDING)
    .limit(20)
    .offset(0)
    .return_as(ReturnType.DICT)
)
```

## Writes

### `create(**kwargs)`

Creates one row and returns a model instance.

- `auto_now_add_fields` are set before insert when field value is `None`.
- `auto_generated_fields` are excluded from insert values.
- Current implementation always performs plain `INSERT ... RETURNING`; passed `on_conflict` args are currently not applied.

### `bulk_create(values, skip_validations=False, on_conflict=None, ...)`

Creates many rows.

- Raises `NothingToCreateError` if `values` is empty.
- Supports:
  - `OnConflict.DO_NOTHING`
  - `OnConflict.UPDATE` (requires `conflict_target` and `update_fields`)

### `get_or_create(defaults, **lookup)` and `update_or_create(defaults, **lookup)`

Return tuple `(obj, created)`.

## `update(...)` operators

Standard set update:

```python
await Product.async_queryset.filter(id=1).update(name="New Name")
```

Special suffixes:

- Arithmetic: `__add`, `__sub`, `__mul`, `__div`
- Time interval: `__add_time`, `__sub_time`
- JSONB replace: `__jsonb`
- JSONB key set: `__jsonb_set__key_name`
- JSONB key remove: `__jsonb_remove`

Example:

```python
await Product.async_queryset.filter(id=1).update(
    stock_quantity__add=5,
    properties__jsonb_set__color="blue",
)
```

## `delete()`

Deletes rows matching current filters.

```python
deleted_count = await Product.async_queryset.filter(id=1).delete()
```

## Important safety note

Always call `filter(...)` before `update(...)` or `delete(...)`.
That guarantees valid `WHERE` conditions in generated SQL.

## Connection selection

`using(conn_name)` overrides read connection for the query:

```python
items = await Product.async_queryset.using("replica_1").all()
```
