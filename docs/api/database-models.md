# DatabaseModel

Reference for the `DatabaseModel` base class and related helpers.

## Attributes

- `async_queryset` – descriptor returning an `AsyncQuerySet` bound to the model.
- `model_config` – defaults to `ConfigDict(extra="allow")`, enabling unknown
  columns (useful for `SELECT` statements with computed fields).

## Instance methods

### `save(columns: list[str] | None = None) -> bool`

Update the current row in the database. When `columns` is omitted, all fields on
the model are persisted. Returns `True` if at least one row was updated.

### `delete() -> bool`

Delete the current row and return whether a row was removed.

Both methods rely on the `Meta.primary_key` value to build the `WHERE` clause.

## Meta configuration

| Option | Description |
|--------|-------------|
| `db_table` | Name of the table to query. Required. |
| `primary_key` | Name of the primary key column. Defaults to `"id"`. |
| `auto_generated_fields` | Sequence of fields removed from insert statements. |
| `auto_now_add_fields` | Sequence of fields populated once during insert. |
| `auto_now_fields` | Sequence of fields refreshed each time `save()` runs. |
| `relations` | Dict mapping relation names to `Relation` objects. |

## Queryset property

`queryset_property` is a descriptor similar to `@property` but designed for
classes. It powers the `async_queryset` attribute and can be reused to expose
custom querysets on your own classes if needed.
