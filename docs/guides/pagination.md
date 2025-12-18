# Pagination

FastPG includes two helper classes for paginating results: `AsyncPaginator` for
querysets and `RawQueryAsyncPaginator` for raw SQL queries. Both expose a common
API that returns a payload containing the results and metadata about the current
page.

## Paginating querysets

```python
from fastpg import AsyncPaginator

queryset = Customer.async_queryset.filter(is_active=True).order_by(created_at="DESC")
paginator = AsyncPaginator(page_size=20, queryset=queryset)

first_page = await paginator.get_page(page=1)
second_page = await paginator.get_next_page()
```

The response structure looks like this:

```json
{
  "results": [...],
  "results_paginator": {
    "number": 1,
    "page_size": 20,
    "has_next": true,
    "has_previous": false,
    "start_index": 0,
    "end_index": 20
  }
}
```

`get_next_page()` and `get_previous_page()` automatically adjust the current
page number and call `get_page()` internally. If you request a page number less
than 1, the paginator raises `InvalidPageError`. When a page contains no
results, `start_index` and `end_index` are set to `null`.

## Paginating raw SQL

Sometimes you may want to page the results of a handcrafted SQL statement. Use
`RawQueryAsyncPaginator` with a query string that contains `{limit}` and
`{offset}` placeholders.

```python
from fastpg import RawQueryAsyncPaginator

query = """
SELECT id, email
FROM customers
WHERE created_at >= :start
ORDER BY created_at DESC
LIMIT {limit} OFFSET {offset}
"""

paginator = RawQueryAsyncPaginator(
    page_size=50,
    query=query,
    values={"start": window_start},
)
page = await paginator.get_page(1)
```

Optionally provide a `serializer` callable to transform the records returned
from the database before they are included in the paginator payload. See the
[API reference](../api/queries.md#asyncqueryset) for return types and
[RawQueryAsyncPaginator](../api/queries.md#asyncrawquery) for configuration
details.
