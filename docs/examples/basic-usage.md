# Basic Usage

This example mirrors the `test_project` shop schema.

```python
from fastpg import DatabaseModel, JsonData, OnConflict, OrderBy


class Category(DatabaseModel):
    id: int | None = None
    name: str
    description: str

    class Meta:
        db_table = "categories"
        primary_key = "id"
        auto_generated_fields = ["id"]


class Product(DatabaseModel):
    id: int | None = None
    sku: str
    name: str
    category_id: int | None = None
    price: float
    stock_quantity: int
    properties: JsonData = {}

    class Meta:
        db_table = "products"
        primary_key = "id"
        auto_generated_fields = ["id"]
```

Bulk upsert-like sync with `bulk_create`:

```python
payload = [
    {
        "sku": "SKU-1",
        "name": "Cap",
        "category_id": 1,
        "price": 15.0,
        "stock_quantity": 10,
        "properties": {"color": "black"},
    },
    {
        "sku": "SKU-2",
        "name": "Tee",
        "category_id": 1,
        "price": 20.0,
        "stock_quantity": 8,
        "properties": {"size": "L"},
    },
]

await Product.async_queryset.bulk_create(
    values=payload,
    on_conflict=OnConflict.UPDATE,
    conflict_target=["sku"],
    update_fields=["name", "category_id", "price", "stock_quantity", "properties"],
)
```

Read and mutate:

```python
products = await Product.async_queryset.all().order_by(id=OrderBy.ASCENDING)

await Product.async_queryset.filter(id=1).update(stock_quantity__add=5)
await Product.async_queryset.filter(id=1).update(properties__jsonb_set__color="blue")
```
