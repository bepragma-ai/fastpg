# Querysets

`AsyncQuerySet` builds SQL lazily and executes only when awaited.

## Execution Model

A queryset becomes awaitable after one of these terminal actions sets the operation:

- `get(...)`
- `filter(...)`
- `all()`
- `count()`
- `update(...)`
- `delete()`

Awaiting a queryset with no action raises `MalformedQuerysetError`.

## Basic Reads

```python
user = await User.async_queryset.get(id=1)
users = await User.async_queryset.filter(name__icontains="ada")
all_users = await User.async_queryset.all()
total = await User.async_queryset.filter(is_active=True).count()
```

`get(...)` returns one record or raises `DoesNotExist` / `MultipleRecordsFound`.

## Lookup Operators

Supported filter suffixes:

- `__gt`, `__lt`, `__gte`, `__lte`, `__ne`
- `__in`
- `__isnull`
- `__contains`, `__icontains`
- `__startswith`, `__istartswith`
- `__endswith`, `__iendswith`

Notes:

- `__in` requires a non-empty Python `list`.
- `__isnull=True` renders `IS NULL`; `False` renders `IS NOT NULL`.

## `Q` Objects

```python
from fastpg import Q

q = Q(city="Boston") | Q(city="New York")
rows = await Customer.async_queryset.filter(q, is_active=True)
```

Positional `Q(...)` objects and keyword filters are combined with `AND`.

## Selecting Columns and Return Type

```python
from fastpg import OrderBy, ReturnType

rows = await (
    Product.async_queryset
    .columns("id", "name", "price")
    .filter(price__gte=100)
    .order_by(price=OrderBy.DESCENDING)
    .return_as(ReturnType.DICT)
)
```

Use `return_as(ReturnType.DICT)` when fetching partial columns unless the omitted model fields all have defaults. Model-instance hydration still goes through the model constructor.

## Read Connection Selection

```python
rows = await Product.async_queryset.using("replica_1").all()
```

`using(conn_name)` only changes the read connection used by that queryset.

## Write Helpers

### `create(**kwargs)`

Creates one row and returns a model instance.

- `auto_now_add_fields` are populated before insert when the field is `None`.
- `auto_generated_fields` are removed from the insert payload.
- Conflict handling is not part of `create()`.

### `bulk_create(values, on_conflict, conflict_target=None, update_fields=None, skip_validations=False)`

Creates multiple rows with one statement template executed through `execute_many()`.

```python
from fastpg import OnConflict

await Product.async_queryset.bulk_create(
    values=products_batch,
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "category_id", "price", "stock_quantity"],
)
```

Behavior:

- `values=[]` raises `NothingToCreateError`.
- `OnConflict.DO_NOTHING` adds `ON CONFLICT DO NOTHING`.
- `OnConflict.UPDATE` requires both `conflict_target` and `update_fields`.
- Passing `None` for `on_conflict` produces a plain batch insert with no conflict clause.
- `skip_validations=True` uses `model_construct(...)` instead of normal Pydantic validation.

### `get_or_create(defaults, **lookup)`

Fetches a row by `lookup` or creates one from `{**lookup, **defaults}`.

Returns `(obj, created)`.

### `update_or_create(defaults, **lookup)`

Fetches a row by `lookup`, updates it with `defaults` via model `save()`, or creates a new row.

Returns `(obj, created)`.

## `update(...)`

Always start with a filtered queryset:

```python
updated = await Product.async_queryset.filter(id=1).update(name="New Name")
```

Supported update suffixes:

- Arithmetic: `__add`, `__sub`, `__mul`, `__div`
- Time intervals: `__add_time`, `__sub_time`
- JSONB replace: `__jsonb`
- JSONB set key: `__jsonb_set__key_name`
- JSONB remove key: `__jsonb_remove`

Example:

```python
await Product.async_queryset.filter(id=1).update(
    stock_quantity__add=5,
    properties__jsonb_set__color="blue",
)
```

## `delete()`

Always start with a filtered queryset:

```python
deleted = await Product.async_queryset.filter(id=1).delete()
```

## Safety Note

`UnrestrictedUpdateError` and `UnrestrictedDeleteError` exist for unsafe mutations, but the current queryset flow should still be treated as "filter first, then mutate" to guarantee valid SQL generation.
