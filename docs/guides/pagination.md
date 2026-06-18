# Pagination

FastPG provides:

- `AsyncPaginator` for `AsyncQuerySet`
- `RawQueryAsyncPaginator` for raw SQL

Both return this shape:

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

## `AsyncPaginator`

```python
from fastpg import AsyncPaginator, OrderBy

paginator = AsyncPaginator(
    page_size=25,
    queryset=Product.async_queryset.all().order_by(id=OrderBy.ASCENDING),
)

page1 = await paginator.get_page(page=1)
page2 = await paginator.get_next_page()
```

Behavior:

- `page` must be `>= 1`, otherwise `InvalidPageError`.
- `get_page()` applies `limit(page_size)` and `offset((page - 1) * page_size)`.
- Pass `using="replica_1"` to run on a specific read connection.

Metadata notes:

- `has_next` is inferred from whether the current page returned exactly `page_size` rows.
- `start_index` is zero-based.
- `end_index` is `start_index + object_count`.

## `RawQueryAsyncPaginator`

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

Behavior:

- `auto_offset_and_limit=True` appends `LIMIT ... OFFSET ...`.
- `auto_offset_and_limit=False` expects `{page_size}` and `{offset}` placeholders inside your query string.
- `serializer` runs after the raw fetch and before the paginator response is built.
