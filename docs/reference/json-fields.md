# JSON Fields

FastPG exposes JSON helpers in `fastpg.fields`.

## `JsonData`

`JsonData` is an annotated Pydantic type for JSON-compatible values.

```python
from fastpg import DatabaseModel, JsonData


class Product(DatabaseModel):
    id: int | None = None
    properties: JsonData = {}

    class Meta:
        db_table = "products"
        primary_key = "id"
        auto_generated_fields = ["id"]
```

Behavior:

- Dicts and lists are serialized to JSON strings during DB writes.
- Normal model usage keeps Python values as dict/list objects.
- `CustomJsonEncoder` serializes `datetime` values with `isoformat()`.

## Helper Functions

- `json_str_to_dict(value)`
  Parses JSON strings returned from the database and leaves non-string values unchanged.
- `validate_json_data(data)`
  Converts dict/list values to JSON during validation.
- `serialize_json_data(data, info)`
  Returns JSON strings only when `info.context["db_write"]` is truthy.

## JSONB Update Operators

FastPG supports these queryset update forms:

- `field__jsonb={...}`
- `field__jsonb_set__key=value`
- `field__jsonb_remove="key"`

Example:

```python
await Product.async_queryset.filter(id=1).update(
    properties__jsonb_set__color="blue",
)
```
