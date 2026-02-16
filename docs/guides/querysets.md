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

## Query shaping

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
