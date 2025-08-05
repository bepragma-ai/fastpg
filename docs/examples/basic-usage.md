# Basic Usage

```python
from fastpg import DatabaseModel, AsyncPaginator

class Book(DatabaseModel):
    id: int
    title: str

    class Meta:
        db_table = "books"

# Create
await Book.objects.create(id=1, title="1984")

# Read
book = await Book.objects.get(id=1).fetch()

# Update
await Book.objects.filter(id=1).update(title="Animal Farm").execute()

# Delete
await Book.objects.filter(id=1).delete().execute()

# Pagination
paginator = AsyncPaginator(page_size=10, queryset=Book.objects.all())
page1 = await paginator.get_page(1)
```

Handle errors using built-in exceptions like `DoesNotExist` and
`MultipleRecordsFound`.

