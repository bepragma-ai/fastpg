# Basic Usage

This example follows the same patterns used in `test_project`.

```python
from fastpg import DatabaseModel, JsonData


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

Create and fetch:

```python
product = await Product.async_queryset.create(
    sku="SKU-1",
    name="Cap",
    category_id=1,
    price=15.0,
    stock_quantity=10,
    properties={"color": "black"},
)

same_product = await Product.async_queryset.get(id=product.id)
products = await Product.async_queryset.all()
```

Bulk upsert:

```python
from fastpg import OnConflict

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

Update fields in place:

```python
await Product.async_queryset.filter(id=1).update(stock_quantity__add=5)
await Product.async_queryset.filter(id=1).update(properties__jsonb_set__color="blue")
```
