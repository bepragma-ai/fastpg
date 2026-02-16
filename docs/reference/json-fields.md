# JSON Fields

FastPG includes JSON helpers in `fastpg.fields`.

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

- For DB writes (`model_dump(context={"db_write": True})`), dict/list values are serialized to JSON.
- For normal serialization, Python objects are preserved.

## Helper functions

- `json_str_to_dict(value)`: if `value` is a JSON string, parse it.
- `validate_json_data(data)`: serialize dict/list values for validation flow.
- `serialize_json_data(data, info)`: serializer used by `JsonData`.

## JSON update operators in queryset `update(...)`

- `field__jsonb={...}`: replace JSONB column.
- `field__jsonb_set__key=value`: set one JSON key.
- `field__jsonb_remove="key"`: remove one JSON key.

Example:

```python
await Product.async_queryset.filter(id=1).update(
    properties__jsonb_set__color="blue",
)
```
