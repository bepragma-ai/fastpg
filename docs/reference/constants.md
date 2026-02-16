# Constants And Helpers

## Enums/constants

### `ConnectionType`

- `ConnectionType.READ`
- `ConnectionType.WRITE`

### `OrderBy`

- `OrderBy.ASCENDING` (`"ASC"`)
- `OrderBy.DESCENDING` (`"DESC"`)

### `OnConflict`

- `OnConflict.DO_NOTHING`
- `OnConflict.UPDATE`

### `ReturnType`

- `ReturnType.MODEL_INSTANCE`
- `ReturnType.DICT`

## Relationship helpers

### `Relation(related_model, foreign_field, related_name=None)`

Defines join metadata for `select_related`.

### `Prefetch(dataset_name, queryset)`

Defines prefetch metadata for `prefetch_related`.

## Query helper

### `Q(...)`

Builds reusable SQL where fragments with supported lookup operators and supports `&` / `|` composition.
