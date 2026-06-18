# Constants And Helpers

## Constants

### `ConnectionType`

- `ConnectionType.READ`
- `ConnectionType.WRITE`

### `OrderBy`

- `OrderBy.ASCENDING`
- `OrderBy.DESCENDING`

These render to `ASC` and `DESC`.

### `OnConflict`

- `OnConflict.DO_NOTHING`
- `OnConflict.UPDATE`

Used by `bulk_create(...)`.

### `ReturnType`

- `ReturnType.MODEL_INSTANCE`
- `ReturnType.DICT`

Used by queryset `return_as(...)`.

## Relationship Helpers

### `Relation(related_model, foreign_field, related_name=None)`

Stores join metadata for `select_related(...)`.

- `related_model` is the joined model class.
- `foreign_field` is the foreign-key column on the base model.
- `related_name` overrides the attribute/key name attached to the result.

### `Prefetch(dataset_name, queryset)`

Stores child-collection metadata for `prefetch_related(...)`.

- `dataset_name` becomes the attached attribute or dict key.
- `queryset` is the child model queryset to execute for the prefetch.

## Query Helpers

### `Q(...)`

Builds reusable SQL `WHERE` fragments and supports `&` / `|` composition.

### `InClauseParam(values)`

Expands a single named raw-query parameter into multiple bound values for `IN (...)` clauses.
