# Query API

## `AsyncQuerySet(model)`

Primary query builder for model reads and writes.

### Query Construction

| Method | Purpose |
| --- | --- |
| `using(conn_name)` | Override the read connection for this queryset. |
| `columns(*columns)` | Select declared model fields; use dict results for partial records. |
| `get(*args, **kwargs)` | Fetch one matching row. |
| `filter(*args, **kwargs)` | Fetch many matching rows. |
| `all()` | Select rows and clear base filters; related filters and other modifiers remain. |
| `count()` | Count all rows matching base and related filters, ignoring ordering and pagination. |
| `order_by(**order_by)` | Order declared fields using `OrderBy.ASCENDING` or `OrderBy.DESCENDING`. |
| `limit(fetch_limit)` | Set a non-negative integer limit; zero returns no rows. |
| `offset(fetch_offset)` | Set a non-negative integer offset. |
| `return_as(return_type)` | Return model instances or dicts for read queries. |
| `lock_for_update()` | Lock filtered base rows on the write connection inside a transaction. |

`lock_for_update()` requires `filter(...)` and returns a list. It supports
`select_related()` but rejects `get()`, prefetching, ordering, limits, and offsets.
See [row locks and the contention test](../guides/transactions.md#row-locks).

### Relationship Helpers

| Method | Purpose |
| --- | --- |
| `select_related(*relation_names)` | Join configured relations and hydrate them. |
| `filter_related(*args, **kwargs)` | Add `WHERE` clauses for the joined related table. |
| `prefetch_related(*prefetches)` | Fetch child collections in follow-up queries. |

### Write Helpers

| Method | Purpose |
| --- | --- |
| `create(**kwargs)` | Insert one row and return the model instance. |
| `bulk_create(values, on_conflict, conflict_target=None, update_fields=None, skip_validations=False)` | Batch insert or upsert; `on_conflict` is required, and the method returns `None`. |
| `get_or_create(defaults, **kwargs)` | Fetch one row or create it. |
| `update_or_create(defaults, **kwargs)` | Update an existing row or create it. |
| `update(**kwargs)` | Build an update query for the current filtered queryset. |
| `delete()` | Build a delete query for the current filtered queryset. |

### Raw Execution Helper

- `execute_raw_query(query, values)`
  Runs a raw read query through the queryset's current read connection and returns serialized results.

### Await Behavior

The first successful await executes SQL and returns:

- `get()` -> one model instance or dict
- `filter()` / `all()` -> list
- `count()` -> integer
- `update()` / `delete()` -> integer affected-row count

Querysets are mutable. Subsequent awaits return the cached result until a query
modifier is called. This also prevents an unchanged write from executing twice.
Create a fresh queryset for an independent query or a new locking transaction.

`create()`, `bulk_create()`, `get_or_create()`, `update_or_create()`, and
`execute_raw_query()` are async methods that execute when their own coroutine is
awaited; they do not use the queryset's result cache to skip their work.

## `AsyncRawQuery(query, using=None)`

Wrapper for hand-written SQL with FastPG error handling.

`using` overrides only the read connection used by `fetch()`. `execute()` and
`execute_many()` use the configured write connection. Supply values through bind
parameters; the SQL text itself is application-controlled.

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

Use a fresh `AsyncRawQuery` for each execution with `InClauseParam`: expansion
modifies the stored SQL. Values must be non-empty lists.

## `AsyncPaginator(page_size, queryset, using=None, serializer=None)`

Paginator for `AsyncQuerySet`.

`serializer`, when supplied, is a synchronous callable applied to fetched records.

- `get_page(page=1, context=None)`
- `get_next_page()`
- `get_previous_page()`

## `RawQueryAsyncPaginator(page_size, query, values, serializer=None, auto_offset_and_limit=True, using=None)`

Paginator for raw SQL with optional serializer and optional automatic `LIMIT` / `OFFSET` handling.
