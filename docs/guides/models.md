# Models

All FastPG models inherit from `DatabaseModel`, which extends `pydantic.BaseModel`.

## Model Definition

```python
from datetime import datetime
from fastpg import DatabaseModel


class Department(DatabaseModel):
    id: int | None = None
    name: str
    location: str
    created_at: datetime | None = None

    class Meta:
        db_table = "departments"
        primary_key = "id"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["created_at"]
```

## `Meta` Options

| Option | Required | Meaning |
| --- | --- | --- |
| `db_table` | Yes | PostgreSQL table name. |
| `primary_key` | Yes | Primary key column used by `save()`, `delete()`, `count()`, and insert return handling. |
| `auto_generated_fields` | No | Fields removed from insert payloads before `create()` and `bulk_create()`. |
| `auto_now_add_fields` | No | Fields filled with `datetime.now(fastpg.TZ)` during create flows when the current value is `None`. |
| `auto_now_fields` | No | Fields filled with `datetime.now(fastpg.TZ)` before `save()` when the current value is `None`. |
| `relations` | No | Mapping of relation name to `Relation(...)`. |

## Class-Level Accessor

`async_queryset` is a descriptor on the model class:

```python
rows = await Department.async_queryset.all()
```

Each access returns a fresh `AsyncQuerySet` bound to the current FastPG instance.

## Instance Hooks

Override these when you need model-specific save hooks:

```python
class Department(DatabaseModel):
    ...

    async def pre_save(self) -> None:
        ...

    async def post_save(self) -> None:
        ...
```

`save()` calls `pre_save()` before the update query and `post_save()` only if the update succeeds.

## Instance Methods

### `save(columns: list[str] | None = None) -> bool`

Updates the row identified by `Meta.primary_key`.

- Returns `True` when at least one row is updated.
- If `columns` is omitted, FastPG includes every field from `model_dump(...)` in the `SET` clause.
- `auto_now_fields` are only filled when the current field value is `None`.

### `delete() -> bool`

Deletes the row identified by `Meta.primary_key` and returns whether a row was deleted.

## JSON Columns

Use `JsonData` for JSON or JSONB-backed fields:

```python
from fastpg import DatabaseModel, JsonData


class Product(DatabaseModel):
    id: int | None = None
    name: str
    properties: JsonData = {}

    class Meta:
        db_table = "products"
        primary_key = "id"
        auto_generated_fields = ["id"]
```

`JsonData` keeps Python dict/list values in normal model use and serializes them when FastPG prepares DB writes.
