# Quickstart

This quickstart demonstrates defining a model, creating the database tables,
performing CRUD operations, and paginating results.

```python
from fastpg import DatabaseModel, ASYNC_CUSTOMERS_DB_WRITE

class Item(DatabaseModel):
    id: int
    name: str

    class Meta:
        db_table = "items"

async def main():
    # Create a record
    await ASYNC_CUSTOMERS_DB_WRITE.execute(
        "INSERT INTO items(id, name) VALUES (:id, :name)",
        {"id": 1, "name": "Widget"},
    )

    # Query records
    results = await Item.async_queryset.all()
    print(results)
```

