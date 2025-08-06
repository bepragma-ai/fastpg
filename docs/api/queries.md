# Queries

`AsyncQuerySet` provides a chainable API for building SQL queries.

## Retrieving records

```python
# Get a single record
await User.async_queryset.get(id=1)

# Filter multiple records
users = await User.async_queryset.filter(age__gte=18)
```

- `__gt`, `__gte`, `__lt`, `__lte` – comparison operators
- `__in` – membership, expects a list
- `__or` – combine conditions with OR using `Q` objects

## Aggregation

```python
count = await User.async_queryset.filter(active=True).count()
```

## Updating and deleting

```python
# Update
await User.async_queryset.filter(id=1).update(name="New")

# Delete
await User.async_queryset.filter(id=1).delete()
```

