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

`MalformedQuerysetError` also covers unsupported `lock_for_update()` combinations.
Query modifiers raise `ValueError` for unknown selected/updated/ordered fields,
invalid ordering directions, invalid limits or offsets, and empty `update()` calls.
Missing required arguments and incomplete `OnConflict.UPDATE` options raise `TypeError`.
Pydantic validation errors can occur while creating or hydrating models.

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

Driver errors with a SQLSTATE are wrapped in `DatabaseError`, exposing `.sqlstate`,
`.name`, and a formatted `.message`. Errors without a SQLSTATE propagate unchanged.

`DuplicateKeyDatabaseError` specializes unique-constraint failures (`23505`) from
`create()`, `bulk_create()`, and raw writes. Its `.message` includes the driver
message and table context when available. Ordinary queryset updates and model
saves wrap these failures as `DatabaseError`; inspect `.sqlstate` to distinguish them.
