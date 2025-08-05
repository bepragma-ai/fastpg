# Queries

`AsyncQuerySet` provides a chainable API for building SQL queries.

## Retrieving records

```python
# Get a single record
await User.objects.get(id=1).fetch()

# Filter multiple records
users = await User.objects.filter(age__gte=18).fetch()
```

- `__gt`, `__gte`, `__lt`, `__lte` – comparison operators
- `__in` – membership, expects a list
- `__or` – combine conditions with OR using `Q` objects

## Aggregation

```python
count = await User.objects.filter(active=True).count().fetch()
```

## Updating and deleting

```python
# Update
await User.objects.filter(id=1).update(name="New").execute()

# Delete
await User.objects.filter(id=1).delete().execute()
```

