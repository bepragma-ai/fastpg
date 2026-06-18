# Database Models API

## `DatabaseModel`

Base class for all FastPG models.

### Class Attributes

- `async_queryset`
  Returns a fresh `AsyncQuerySet(model=cls)` bound to the current FastPG instance.
- `write_connection`
  Set from `get_fastpg().db_conn_manager.db_for_write()` when `async_queryset` is accessed.

### Hooks

- `async pre_save() -> None`
- `async post_save() -> None`

Both are no-op by default and can be overridden on the model class.

### Methods

#### `async save(columns: list[str] | None = None) -> bool`

Updates the current row by primary key.

- Calls `pre_save()` before the update query.
- Applies `auto_now_fields` when the current field value is `None`.
- Calls `post_save()` only when at least one row is updated.

#### `async delete() -> bool`

Deletes the current row by primary key and returns whether the delete affected a row.

### Required `Meta` Members

- `db_table`
- `primary_key`

### Optional `Meta` Members

- `auto_generated_fields`
- `auto_now_add_fields`
- `auto_now_fields`
- `relations`

## `queryset_property`

Descriptor used internally to expose `DatabaseModel.async_queryset` as a class-level accessor.

## `Transaction`

Utility wrapper around the current FastPG write connection transaction.

### Methods

- `Transaction.atomic()`
- `await Transaction.start()`
- `Transaction.decorator()`
