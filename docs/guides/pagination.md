# Pagination

FastPG provides two paginator classes:

- `AsyncPaginator` for `AsyncQuerySet`
- `RawQueryAsyncPaginator` for raw SQL

Both return the same shape:

```json
{
  "results": [],
  "results_paginator": {
    "number": 1,
    "page_size": 20,
    "has_next": false,
    "has_previous": false,
    "start_index": 0,
    "end_index": 0
  }
}
```

## Queryset pagination

```python
from fastpg import AsyncPaginator, OrderBy

queryset = Product.async_queryset.all().order_by(id=OrderBy.ASCENDING)
paginator = AsyncPaginator(page_size=25, queryset=queryset)

page1 = await paginator.get_page(page=1)
page2 = await paginator.get_next_page()
```

Rules:

- `page` must be `>= 1`, else `InvalidPageError`.
- `get_page()` applies `limit(page_size)` and computed `offset(...)`.
- Pass `using="conn_name"` to execute on a specific read connection.

## Raw SQL pagination

```python
from fastpg import RawQueryAsyncPaginator

paginator = RawQueryAsyncPaginator(
    page_size=50,
    query="SELECT id, sku FROM products ORDER BY id",
    values={},
    serializer=lambda rows: [{"id": r["id"], "sku": r["sku"]} for r in rows],
)

page = await paginator.get_page(page=1)
```

`RawQueryAsyncPaginator` behavior:

- `auto_offset_and_limit=True` (default): appends `LIMIT ... OFFSET ...` automatically.
- `auto_offset_and_limit=False`: your query must include `{page_size}` and `{offset}` placeholders.
