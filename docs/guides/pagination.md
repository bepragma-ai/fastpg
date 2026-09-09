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
    "start_index": null,
    "end_index": null
  }
}
```

## `AsyncPaginator`

```python
from fastpg import AsyncPaginator, OrderBy
from app.schemas.shop import Product

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
- These modifiers invalidate the queryset cache, so each requested page is fetched.
- Pass `using="replica_1"` to run on a specific read connection.
- Use a positive integer `page_size` and stable ordering, such as the primary key.
- An optional synchronous `serializer` transforms the fetched records.

Metadata notes:

- `has_next` is inferred from whether the current page returned exactly `page_size` rows.
- A full final page therefore reports `has_next=True`; the next request may be empty.
- `start_index` is zero-based.
- `end_index` is exclusive: `start_index + object_count`.
- Empty fetched pages use `None` (`null` in JSON) for both indexes. The separate
  `BasePaginator.get_empty_data_response()` helper uses zero for both indexes.
- `context` is merged into the top-level response; avoid overwriting `results`
  or `results_paginator` unless that is intentional.

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
