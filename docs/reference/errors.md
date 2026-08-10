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
- `InvalidDatabaseModelUriError`

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
`DuplicateKeyDatabaseError` exposes the original database message as `.message`, which
can be translated into the calling framework's conflict or validation response.
