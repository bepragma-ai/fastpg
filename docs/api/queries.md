# Query API

## `AsyncQuerySet(model)`

Primary query builder for model reads and writes.

### Query Construction

| Method | Purpose |
| --- | --- |
| `using(conn_name)` | Override the read connection for this queryset. |
| `columns(*columns)` | Limit selected columns. |
| `get(*args, **kwargs)` | Fetch one matching row. |
| `filter(*args, **kwargs)` | Fetch many matching rows. |
| `all()` | Fetch all rows. |
| `count()` | Count rows, optionally after existing filters were added. |
| `order_by(**order_by)` | Add `ORDER BY`. |
| `limit(fetch_limit)` | Add `LIMIT`. |
| `offset(fetch_offset)` | Add `OFFSET`. |
| `return_as(return_type)` | Return model instances or dicts for read queries. |

### Relationship Helpers

| Method | Purpose |
| --- | --- |
| `select_related(*relation_names)` | Join one configured relation and hydrate it. |
| `filter_related(*args, **kwargs)` | Add `WHERE` clauses for the joined related table. |
| `prefetch_related(*prefetches)` | Fetch child collections in follow-up queries. |

### Write Helpers

| Method | Purpose |
| --- | --- |
| `create(**kwargs)` | Insert one row and return the model instance. |
| `bulk_create(values, on_conflict, conflict_target=None, update_fields=None, skip_validations=False)` | Batch insert or upsert. |
| `get_or_create(defaults, **kwargs)` | Fetch one row or create it. |
| `update_or_create(defaults, **kwargs)` | Update an existing row or create it. |
| `update(**kwargs)` | Build an update query for the current filtered queryset. |
| `delete()` | Build a delete query for the current filtered queryset. |

### Raw Execution Helper

- `execute_raw_query(query, values)`
  Runs a raw read query through the queryset's current read connection and returns serialized results.

### Await Behavior

Awaiting the queryset executes SQL and returns:

- `get()` -> one model instance or dict
- `filter()` / `all()` -> list
- `count()` -> integer
- `update()` / `delete()` -> write-query result, typically an affected-row count

## `AsyncRawQuery(query, using=None)`

Wrapper for hand-written SQL with FastPG error handling.

### Methods

- `fetch(values)` -> list of dict records using a read connection
- `execute(values)` -> execute one write query using the write connection
- `execute_many(list_of_values)` -> execute the same write query for many parameter sets

### `InClauseParam`

Use `InClauseParam([...])` inside raw-query values when a named parameter should expand into an `IN (...)` clause:

```python
from fastpg import AsyncRawQuery, InClauseParam

rows = await AsyncRawQuery(
    query="""
        SELECT * FROM orders
        WHERE id IN (:order_ids)
          AND customer_id IN (:customer_ids)
    """
).fetch(
    values={
        "order_ids": InClauseParam([1, 2, 3]),
        "customer_ids": InClauseParam([10, 11]),
    }
)
```

## `AsyncPaginator(page_size, queryset, using=None)`

Paginator for `AsyncQuerySet`.

- `get_page(page=1, context=None)`
- `get_next_page()`
- `get_previous_page()`

## `RawQueryAsyncPaginator(...)`

Paginator for raw SQL with optional serializer and optional automatic `LIMIT` / `OFFSET` handling.
