# Errors

FastPG defines explicit exception classes in `fastpg.errors`.

## Connection and configuration

- `ReadConnectionNotAvailableError`
- `MultipleWriteConnectionsError`
- `InvalidConnectionNameError`
- `FastPGInstanceNotConfiguredError`
- `MalformedMetaError`
- `MalformedQuerysetError`

## Query construction and operators

- `InvalidINClauseValueError`
- `UnsupportedOperatorError`
- `InvalidRelatedFieldError`
- `InvalidPrefetchError`

## Result shape and cardinality

- `DoesNotExist`
- `MultipleRecordsFound`

## Mutation safety

- `NothingToCreateError`
- `UnrestrictedUpdateError`
- `UnrestrictedDeleteError`

## Pagination

- `InvalidPageError`

## Database execution

- `DatabaseError`
- `DuplicateKeyDatabaseError`

`DatabaseError` includes SQLSTATE and driver exception class name when available.
