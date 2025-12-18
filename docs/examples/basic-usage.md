# Basic usage

The shop demo models provide an end-to-end tour of FastPG. The example below
shows how to model inventory, load related data, and keep products in sync from a
bulk import while staying entirely asynchronous. Links in the comments point to
the relevant guides for deeper reference.

```python
from fastpg import DatabaseModel, AsyncPaginator, OnConflict, OrderBy, ReturnType


class Category(DatabaseModel):
    id: int | None = None
    name: str
    description: str

    class Meta:
        db_table = "categories"
        auto_generated_fields = ["id"]


class Product(DatabaseModel):
    id: int | None = None
    sku: str
    name: str
    category_id: int | None = None
    price: float
    stock_quantity: int

    class Meta:
        db_table = "products"
        auto_generated_fields = ["id"]


# Insert or update a catalogue in one call (see Query API → mutation helpers)
payload = [
    {
        "sku": "HAT-001",
        "name": "Logo Baseball Cap",
        "category_id": 1,
        "price": 19.99,
        "stock_quantity": 50,
    },
    {
        "sku": "HAT-002",
        "name": "Wool Beanie",
        "category_id": 1,
        "price": 24.99,
        "stock_quantity": 80,
    },
]

# [bulk_create](../api/queries.md#mutation-helpers) with conflict handling
await Product.async_queryset.bulk_create(
    payload,
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "category_id", "price", "stock_quantity"],
)

# Read back the range of products, sorted by price descending
products = await Product.async_queryset.order_by(price=OrderBy.DESCENDING)

# Pull a single product as a dict for light-weight serialisation
product_data = await (
    Product.async_queryset
    .filter(sku="HAT-001")
    .return_as(ReturnType.DICT)
)

# Paginate the catalogue for an API response (see [pagination guide](../guides/pagination.md))
queryset = Product.async_queryset.all().order_by(name=OrderBy.ASCENDING)
paginator = AsyncPaginator(page_size=10, queryset=queryset)
page1 = await paginator.get_page(1)
```

`page1["results"]` contains a list of `Product` instances. The paginator
metadata (total count, page boundaries) lives under `page1["results_paginator"]`,
which can be returned directly from a FastAPI route. For details on return
formats, see [`return_as`](../api/queries.md#changing-the-return-format).
