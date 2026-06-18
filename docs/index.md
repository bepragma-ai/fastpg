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
- `update()` and `delete()` should always be chained after `filter(...)`. The safe pattern is required by the current implementation.
- `select_related()` uses one relation at a time and only the first supplied relation name is used.

## Minimal Example

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

- `getting-started.md`
- `guides/models.md`
- `guides/querysets.md`
- `guides/relationships.md`
- `guides/pagination.md`
- `guides/transactions.md`
