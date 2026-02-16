# Query API

## `AsyncQuerySet(model)`

Main query builder for model operations.

### Core methods

- `using(conn_name)`
- `columns(*columns)`
- `get(*conditions, **filters)`
- `filter(*conditions, **filters)`
- `all()`
- `count()`
- `order_by(**order_by)`
- `limit(fetch_limit)`
- `offset(fetch_offset)`
- `return_as(return_type)`

### Relationship methods

- `select_related(*relation_names)`
- `filter_related(*conditions, **filters)`
- `prefetch_related(*prefetches)`

### Mutation methods

- `create(on_conflict=None, conflict_target=None, update_fields=None, **kwargs)`
- `bulk_create(values, skip_validations=False, on_conflict=None, conflict_target=None, update_fields=None)`
- `get_or_create(defaults, **kwargs)`
- `update_or_create(defaults, **kwargs)`
- `update(**kwargs)`
- `delete()`

### Await behavior

Awaiting queryset executes SQL and returns based on action:

- `get()` -> one model/dict, or raises cardinality errors.
- `filter()` / `all()` -> list.
- `count()` -> integer.
- `update()` / `delete()` -> affected row count from write query.

## `AsyncRawQuery(query, using=None)`

Raw SQL wrapper with FastPG error handling.

### Methods

- `fetch(values)` -> list of dict records (read connection)
- `execute(values)` -> execute single write query
- `execute_many(list_of_values)` -> execute write query with many parameter sets

## `AsyncPaginator(page_size, queryset, using=None)`

Paginates an `AsyncQuerySet` and returns `results` plus `results_paginator` metadata.

## `RawQueryAsyncPaginator(...)`

Paginates raw SQL with optional serializer and auto `LIMIT/OFFSET` handling.
