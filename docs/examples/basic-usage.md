# Basic usage

The snippet below demonstrates the lifecycle of a simple `Book` model, including
CRUD operations and pagination.

```python
from fastpg import DatabaseModel, AsyncPaginator

class Book(DatabaseModel):
    id: int | None = None
    title: str
    author: str

    class Meta:
        db_table = "books"
        auto_generated_fields = ["id"]
        auto_now_add_fields = []
        auto_now_fields = []

# Create
book = await Book.async_queryset.create(title="1984", author="George Orwell")

# Read
book = await Book.async_queryset.get(id=book.id)

# Update
await Book.async_queryset.filter(id=book.id).update(title="Animal Farm")

# Delete
await Book.async_queryset.filter(id=book.id).delete()

# Pagination
queryset = Book.async_queryset.all().order_by(title="ASC")
paginator = AsyncPaginator(page_size=10, queryset=queryset)
page1 = await paginator.get_page(1)
```

`page1["results"]` contains a list of `Book` instances; the paginator metadata
is available under the `results_paginator` key.
