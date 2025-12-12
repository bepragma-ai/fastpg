# Query API

The query API comprises `AsyncQuerySet` for model-bound operations and
`AsyncRawQuery` for ad-hoc SQL.

## AsyncQuerySet

### Creation helpers

| Method | Purpose |
|--------|---------|
| `create(**kwargs)` | Insert a single row and return the model instance. |
| `bulk_create(values, skip_validations=False, on_conflict=None, ...)` | Batch insert. Supports `OnConflict.DO_NOTHING` and `OnConflict.UPDATE`. |
| `get_or_create(defaults=None, **lookup)` | Return an existing row or create one from `defaults`. |

### Retrieval helpers

| Method | Purpose |
|--------|---------|
| `get(**filters)` | Fetch a single row. |
| `filter(*conditions, **filters)` | Fetch multiple rows using keyword lookups or `Q` objects. |
| `all()` | Return every row. |
| `count()` | Return the number of matching rows. |
| `columns(*names)` | Select a subset of columns. |
| `order_by(**clauses)` | Accepts a mapping of column → `"ASC"`/`"DESC"`. |
| `limit(n)` / `offset(n)` | Apply pagination clauses. |
| `return_as(ReturnType)` | Switch between model instances and dictionaries. |
| `select_related(*relation_names)` | Join related tables defined in `Meta.relations`. |
| `filter_related(*conditions, **filters)` | Apply filters to the joined tables. |

### Mutation helpers

| Method | Purpose |
|--------|---------|
| `update(**values)` | Update rows matching the current filters. Supports arithmetic (`__add`, `__sub`, `__mul`, `__div`), JSON (`__jsonb`, `__jsonb_set__path`, `__jsonb_remove`), and interval (`__add_time`, `__sub_time`) suffixes. |
| `delete()` | Delete rows matching the filters. |

Awaiting a queryset triggers execution. If no terminal method has been called,
`MalformedQuerysetError` is raised.

## AsyncRawQuery

`AsyncRawQuery` wraps raw SQL statements while still providing consistent error
handling.

| Method | Purpose |
|--------|---------|
| `fetch(values)` | Execute a SELECT-like statement and return dictionaries. |
| `execute(values)` | Execute a modifying statement inside a transaction. |
| `execute_many(list_of_values)` | Execute the same statement with multiple sets of parameters. |

Use raw queries when you need window functions, CTEs, or other constructs that
are easier to express directly in SQL.
