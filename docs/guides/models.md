# Models

`DatabaseModel` extends `pydantic.BaseModel` and is the base class for all FastPG models.

## Model definition

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

## `Meta` options

| Option | Required | Meaning |
| --- | --- | --- |
| `db_table` | Yes | Backing PostgreSQL table name. |
| `primary_key` | No | Primary key column name. |
| `auto_generated_fields` | No | Fields removed before insert. |
| `auto_now_add_fields` | No | Fields auto-populated during create/bulk_create if current value is `None`. |
| `auto_now_fields` | No | Fields auto-populated before `save()` if current value is `None`. |
| `relations` | No | Mapping of relation name to `Relation(...)`. |

## Instance methods

### `save(columns: list[str] | None = None) -> bool`

Updates the current row using `Meta.primary_key` in the `WHERE` clause.

- Returns `True` if at least one row was updated.
- If `columns` is omitted, all model fields are included in `SET`.

### `delete() -> bool`

Deletes the current row by `Meta.primary_key`.

- Returns `True` if at least one row was deleted.

## JSON fields in models

Use `JsonData` for JSON/JSONB columns:

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

`JsonData` serializes dict/list values for DB writes and preserves Python objects in normal model use.
