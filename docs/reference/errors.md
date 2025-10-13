# Errors

FastPG raises descriptive exceptions to help you handle edge cases gracefully.

## Configuration errors

- `MalformedMetaError(model_name)` – raised when a model's `Meta` class is
  missing required attributes such as `db_table` or `primary_key`.
- `MalformedQuerysetError(model_name)` – raised when a queryset is awaited
  without calling one of the terminal methods (`get`, `filter`, `all`, `count`,
  `update`, or `delete`).

## Query construction

- `InvalidINClauseValueError` – raised when the value supplied to `__in` is not a
  non-empty list.
- `UnsupportedOperatorError` – raised when an unknown lookup suffix is used in a
  filter or update expression.

## Result cardinality

- `DoesNotExist` – thrown by `get` when no row matches the filters.
- `MultipleRecordsFound` – thrown by `get` when more than one row matches.

## Mutations

- `DuplicateKeyDatabaseError` – wraps PostgreSQL's `23505` errors during insert
  or update operations.
- `NothingToCreateError` – raised when `bulk_create` is called with an empty
  payload.
- `UnrestrictedUpdateError` / `UnrestrictedDeleteError` – protect against
  accidental full-table updates or deletes by requiring a filter clause.

## Pagination

- `InvalidPageError` – raised when requesting a page number less than 1.

## Database-level failures

- `DatabaseError` – a generic wrapper capturing the underlying exception type
  and SQLSTATE code. Querysets and raw queries raise this when the database
  driver fails or returns an error outside of the specialised cases above.

Handle these exceptions in your application code to return meaningful error
responses or trigger compensating actions.
