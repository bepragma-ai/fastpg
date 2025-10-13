# JSON fields

FastPG provides utilities for working with JSON columns stored in PostgreSQL.

## `JsonData`

Annotate model attributes with `JsonData` to enable automatic serialisation and
deserialisation. The type is defined as an annotated Pydantic `Json` field with
custom validators and serializers.

```python
from fastpg import DatabaseModel, JsonData

class AuditLog(DatabaseModel):
    id: int | None = None
    payload: JsonData

    class Meta:
        db_table = "audit_logs"
```

When a model instance is persisted, FastPG serialises dictionaries and lists to
JSON strings using a custom encoder that understands `datetime` objects. When
reading from the database, JSON strings are converted back to Python objects.

## Helper functions

- `json_str_to_dict(value)` – convert JSON strings into dictionaries; used
  internally when hydrating models.
- `validate_json_data(value)` – serialise Python objects before insert/update.
- `serialize_json_data(value, info)` – honour the `db_write` context flag when
  deciding whether to serialise the data.

You can use these helpers directly if you need to customise behaviour in your
own serializers or background tasks.
