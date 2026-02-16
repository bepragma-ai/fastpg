# FastPG

FastPG is a lightweight async ORM for PostgreSQL built on top of `pydantic` and `databases`.
It keeps SQL explicit, but removes repetitive CRUD and serialization plumbing.

## What FastPG gives you

- Pydantic-based models (`DatabaseModel`) with async CRUD helpers.
- Chainable query builder (`AsyncQuerySet`) with Django-style lookup operators.
- Lightweight relationship loading (`select_related`, `prefetch_related`).
- Bulk inserts with optional PostgreSQL conflict handling.
- JSON field helpers and JSONB update operators.
- Built-in paginators for querysets and raw SQL.
- Transaction helpers and query timing logs.

## Project status notes

This documentation reflects the current source in `src/fastpg`.

- `create(..., on_conflict=...)` currently accepts conflict args but does not apply an `ON CONFLICT` clause.
- `bulk_create(..., on_conflict=...)` does support `OnConflict.DO_NOTHING` and `OnConflict.UPDATE`.
- `update()` and `delete()` should always be chained after `filter(...)` to ensure a valid `WHERE` clause.

## Minimal example

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

## Read next

- `getting-started.md`
- `guides/models.md`
- `guides/querysets.md`
- `guides/relationships.md`
- `guides/pagination.md`
- `guides/transactions.md`
