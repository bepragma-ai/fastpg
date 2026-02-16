# Database Models API

## `DatabaseModel`

Base class for all FastPG models.

### Class attributes

- `async_queryset`: descriptor returning a new `AsyncQuerySet(model=cls)`.
- `write_connection`: populated from the current FastPG instance.

### Methods

#### `async def save(columns: list[str] | None = None) -> bool`

Updates current row by primary key and returns whether any row changed.

#### `async def delete() -> bool`

Deletes current row by primary key and returns whether any row was deleted.

### Required `Meta` members

- `db_table`
- `primary_key`

### Optional `Meta` members

- `auto_generated_fields`
- `auto_now_add_fields`
- `auto_now_fields`
- `relations`

## `queryset_property`

Descriptor used internally for `DatabaseModel.async_queryset`.

## `Transaction`

Utility class exposing write-connection transaction helpers.

### Methods

- `Transaction.atomic()`
- `await Transaction.start()`
- `Transaction.decorator()`
