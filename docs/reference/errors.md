# Errors

FastPG defines explicit exception classes in `fastpg.errors`.

## Configuration And Connection

- `ReadConnectionNotAvailableError`
- `MultipleWriteConnectionsError`
- `InvalidConnectionNameError`
- `FastPGInstanceNotConfiguredError`
- `MalformedMetaError`
- `MalformedQuerysetError`

## Query Construction

- `InvalidINClauseValueError`
- `UnsupportedOperatorError`
- `InvalidRelatedFieldError`
- `InvalidPrefetchError`

## Result Cardinality

- `DoesNotExist`
- `MultipleRecordsFound`

## Write And Pagination

- `NothingToCreateError`
- `UnrestrictedUpdateError`
- `UnrestrictedDeleteError`
- `InvalidPageError`

## Database Execution

- `DatabaseError`
- `DuplicateKeyDatabaseError`

`DatabaseError` wraps the driver error details and includes the SQLSTATE when one is available.
