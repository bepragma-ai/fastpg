# Querysets

`AsyncQuerySet` builds SQL lazily and executes only when awaited.

The examples use models from the configured test project:

```python
from app.schemas.shop import Customer, Employee, Product
```

## Execution Model

A queryset becomes awaitable after one of these terminal actions sets the operation:

- `get(...)`
- `filter(...)`
- `all()`
- `count()`
- `update(...)`
- `delete()`

Awaiting a queryset with no action raises `MalformedQuerysetError`.

Querysets are mutable. Repeatedly awaiting an unchanged queryset returns the
cached result, including the affected-row count for writes. Calling a query
modifier invalidates that cache; the next await executes the modified query.
Use a fresh `Model.async_queryset` when you want an independent query.

```python
query = Employee.async_queryset.filter(salary__gte=50_000)
first = await query
assert await query is first  # No additional SQL.
page = await query.order_by(id="ASC").limit(20)  # Executes the modified query.
```

Chained filters accumulate with `AND`. `all()` clears base filters but retains
related filters, ordering, pagination, and relationship-loading options; it is
not a full reset.

`count()` preserves base and related filters, skips relationship hydration,
and counts all matching rows regardless of ordering, limit, or offset.

## Basic Reads

```python
employee = await Employee.async_queryset.get(id=1)
employees = await Employee.async_queryset.filter(name__icontains="ada")
all_employees = await Employee.async_queryset.all()
total = await Employee.async_queryset.filter(salary__gte=50_000).count()
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
rows = await Customer.async_queryset.filter(q, name__icontains="a")
```

Positional `Q(...)` objects and keyword filters are combined with `AND`.
Generated bind names are unique across `Q` objects. Treat `Q(where_clause=..., params=...)`
as raw SQL: only the supplied parameter values are bound, not the SQL text.

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

Selected and ordered columns must be declared model fields, and ordering
directions must be `ASC` or `DESC`. Limits and offsets must be non-negative
integers; `limit(0)` returns no rows.

## Read Connection Selection

```python
rows = await Product.async_queryset.using("replica_1").all()
```

`using(conn_name)` only changes the read connection used by that queryset.
For read-after-write consistency with the example configuration, use
`.using("default")` to read from the primary. Parent and prefetched child
querysets each have their own read connection; apply `using()` to both when needed.

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

- `on_conflict` is a required argument, including when passing `values=[]`.
- With `on_conflict` supplied, `values=[]` raises `NothingToCreateError`.
- `OnConflict.DO_NOTHING` adds `ON CONFLICT DO NOTHING`.
- `OnConflict.UPDATE` requires both `conflict_target` and `update_fields`.
- Passing `None` for `on_conflict` produces a plain batch insert with no conflict clause.
- `skip_validations=True` uses `model_construct(...)` instead of normal Pydantic validation.
- `conflict_target` must correspond to a database uniqueness constraint or unique index.
- The method returns `None`; it does not return inserted objects or generated IDs.

### `get_or_create(defaults, **lookup)`

Fetches a row by `lookup` or creates one from `{**lookup, **defaults}`.

Returns `(obj, created)`.

### `update_or_create(defaults, **lookup)`

Fetches a row by `lookup`, updates it with `defaults` via model `save()`, or creates a new row.

Returns `(obj, created)`.

Both `get_or_create()` and `update_or_create()` perform a read followed by a
separate write when necessary; they are not PostgreSQL `ON CONFLICT` upserts.
Use `.using("default")` for their lookup when the read replicas may lag.
Concurrent calls can still raise a duplicate-key error; database uniqueness
constraints remain necessary.

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

Pass numeric values for arithmetic and PostgreSQL interval strings such as
`"1 day"` for time updates. SQL expressions are not accepted as update values.

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

Updates and deletes require base or related filters; otherwise they raise
`UnrestrictedUpdateError` or `UnrestrictedDeleteError`. Related filters are
preserved when writing, even though related objects are not hydrated.

Update fields and bulk conflict fields must be declared model fields. Update
values, interval strings, JSON keys, and JSON values are bound parameters.
Only declared model fields are included in insert payloads.

To inspect the SQL that was executed:

```python
query = Employee.async_queryset.filter(salary__gte=50_000)
rows = await query
print(query.query)
```

SQL contains placeholders rather than interpolated values. Placeholder names
are an implementation detail and should not be hard-coded in application code.

## Row Locks

Use `lock_for_update()` with a filtered queryset inside a write transaction:

```python
from fastpg import Transaction

async with Transaction.atomic():
    products = await Product.async_queryset.filter(id=1).lock_for_update()
    if not products:
        raise ValueError("Product not found")
    products[0].stock_quantity += 1
    await products[0].save(columns=["stock_quantity"])
```

The query uses the write connection. `select_related()` is supported and locks
only the base rows (`FOR UPDATE OF t`), while retaining related filters and
hydration. Prefetching, ordering, limits, and offsets are rejected for locking
queries. Locks last for the transaction, so construct a fresh locking queryset
for each transaction.

See [Transactions](transactions.md#row-locks) for restrictions and a runnable
[two-transaction locking test](transactions.md#verify-lock-contention).
