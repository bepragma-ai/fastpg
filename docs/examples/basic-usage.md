# Basic Usage

```python
from fastpg import DatabaseModel, AsyncPaginator

class Book(DatabaseModel):
    id: int
    title: str

    class Meta:
        db_table = "books"

# Create
await Book.async_queryset.create(id=1, title="1984")

# Read
book = await Book.async_queryset.get(id=1)

# Update
await Book.async_queryset.filter(id=1).update(title="Animal Farm")

# Delete
await Book.async_queryset.filter(id=1).delete()

# Pagination
paginator = AsyncPaginator(page_size=10, queryset=Book.async_queryset.all())
page1 = await paginator.get_page(1)
```

Handle errors using built-in exceptions like `DoesNotExist` and
`MultipleRecordsFound`.

