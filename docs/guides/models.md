# Models

`DatabaseModel` is the heart of FastPG. It builds on `pydantic.BaseModel`, so
your database records immediately benefit from Pydantic validation, type hints,
and serialisation helpers.

## Declaring a model

```python
from datetime import datetime
from fastpg import DatabaseModel

class Invoice(DatabaseModel):
    id: int | None = None
    customer_id: int
    total: float
    status: str = "draft"
    issued_at: datetime | None = None
    updated_at: datetime | None = None

    class Meta:
        db_table = "invoices"
        primary_key = "id"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["issued_at"]
        auto_now_fields = ["updated_at"]
```

All fields defined on the model map directly to columns in the backing table.
Default values and `Field` metadata behave just like in a regular Pydantic
model.

## Meta options

| Attribute | Required | Description |
|-----------|----------|-------------|
| `db_table` | ✅ | Name of the table FastPG should query. |
| `primary_key` | ❌ (defaults to `"id"`) | Column used to uniquely identify rows. |
| `auto_generated_fields` | ❌ | Fields that should be omitted on insert (e.g. serial IDs). |
| `auto_now_add_fields` | ❌ | Fields populated with the current timestamp when inserting. |
| `auto_now_fields` | ❌ | Fields refreshed with the current timestamp on `save()`. |
| `relations` | ❌ | Mapping of relation name → `Relation` describing joins. |

The automatic timestamp hooks draw the timezone from the `FASTPG_TZ`
environment variable. Invalid or missing values fall back to UTC.

## Accessing the queryset

Every `DatabaseModel` exposes an `async_queryset` descriptor that returns an
`AsyncQuerySet` bound to the model. The queryset is safe to reuse across
requests because each query call produces a new instance under the hood.

```python
invoices = await Invoice.async_queryset.filter(status="sent")
```

## Instance helpers

Use `save()` to persist modifications to a model instance. Only the columns you
pass will be updated; if omitted, the method updates every field present on the
model.

```python
invoice = await Invoice.async_queryset.get(id=123)
invoice.status = "paid"
await invoice.save(columns=["status"])
```

`delete()` removes the row matching the model's primary key and returns a
boolean indicating whether a record was deleted.

```python
invoice = await Invoice.async_queryset.get(id=123)
await invoice.delete()
```

## Working with JSON columns

If a column stores JSON, annotate it with `JsonData` for transparent
serialisation and deserialisation. FastPG will convert Python objects to JSON
strings when writing and back into Python objects when reading.

```python
from fastpg import JsonData

class Event(DatabaseModel):
    id: int | None = None
    payload: JsonData

    class Meta:
        db_table = "events"
```

## Relationships

Attach lightweight relationships via the `Meta.relations` dictionary. Each entry
contains a `Relation` object that specifies how the current table relates to
another model. See the [relationships guide](relationships.md) for details on
querying related rows.
