# FastPG

FastPG is a lightweight async ORM layer for PostgreSQL applications, especially FastAPI services. It uses `pydantic` models for schema validation and the `databases` package for async I/O, while keeping the generated SQL straightforward.

## What It Includes

- `DatabaseModel` for model definitions and instance-level `save()` / `delete()`
- `AsyncQuerySet` for lazy read and write queries
- `Relation` and `Prefetch` for explicit relationship loading
- `AsyncRawQuery` for hand-written SQL with FastPG error wrapping
- `AsyncPaginator` and `RawQueryAsyncPaginator`
- `Transaction` helpers for the configured write connection

## Important Implementation Notes

- FastPG requires at least one `READ` connection and exactly one `WRITE` connection.
- Single-row `create()` only performs `INSERT ... RETURNING`; conflict handling exists on `bulk_create()`, not on `create()`.
- `update()` and `delete()` require base or related filters and return affected-row counts.
- Unchanged querysets cache their results; query modifiers invalidate that cache.
- `select_related()` supports multiple relations and can be combined with `prefetch_related()`.
- `lock_for_update()` uses the write connection inside a transaction; see [Transactions](guides/transactions.md).

## Minimal Example

Configure FastPG, open its connections, and create the database table before
running this example. FastPG does not create tables or manage migrations.

```python
from fastpg import DatabaseModel


class User(DatabaseModel):
    id: int | None = None
    email: str

    class Meta:
        db_table = "users"
        primary_key = "id"
        auto_generated_fields = ["id"]


async def list_users():
    return await User.async_queryset.all()
```

## Read Next

- [Getting started](getting-started.md)
- [Models](guides/models.md)
- [Querysets](guides/querysets.md)
- [Relationships](guides/relationships.md)
- [Pagination](guides/pagination.md)
- [Transactions and row locks](guides/transactions.md)
- [Running tests](getting-started.md#8-run-the-tests)
