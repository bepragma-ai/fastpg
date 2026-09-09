# Relationships

FastPG relationships are explicit. You describe them in `Meta.relations` and opt into loading strategies per query.

## Define a Relation

```python
from fastpg import DatabaseModel, Relation


class Department(DatabaseModel):
    id: int
    name: str

    class Meta:
        db_table = "departments"
        primary_key = "id"


class Location(DatabaseModel):
    id: int
    office: str

    class Meta:
        db_table = "locations"
        primary_key = "id"


class Employee(DatabaseModel):
    id: int
    department_id: int | None = None
    location_id: int | None = None
    name: str
    salary: float

    class Meta:
        db_table = "employees"
        primary_key = "id"
        relations = {
            "department": Relation(Department, foreign_field="department_id"),
            "location": Relation(Location, foreign_field="location_id"),
        }
```

`foreign_field` is the column on the base model. FastPG renders the join as:

```sql
t.department_id = r.id
```

The related model can be a class or a `"module.Model"` string resolved from FastPG's
model registry. If you omit `related_name`, FastPG derives one from the related model
class name in snake case.

For a string reference such as `"shop.Location"`, import the module defining
that model before evaluating the query. The registry label is the final module
component, or its parent when that component is `models`.

## `select_related(...)`

`select_related()` performs `LEFT JOIN`s and hydrates related objects on each base row.

```python
employee = await Employee.async_queryset.select_related(
    "department", "location"
).get(id=1)
```

Pass multiple relation names to load them in one query. Missing relation names raise
`InvalidRelatedFieldError`.

## `filter_related(...)`

Use `filter_related()` after `select_related()` to add `WHERE` conditions against the joined table:

```python
from fastpg import OrderBy

rows = await (
    Employee.async_queryset
    .select_related("department", "location")
    .filter(salary__gte=50000)
    .filter_related(department__name="Engineering")
    .filter_related(location__office__icontains="london")
    .order_by(salary=OrderBy.DESCENDING)
)
```

`select_related()` takes keys from `Meta.relations`; `filter_related()` prefixes
use the corresponding `Relation.related_name`, which also names the hydrated
attribute. These names match in the examples. Keep them aligned when defining
custom relation names.

Conditions for multiple selected relations can be combined in one call. Using
the test project's order models:

```python
from app.schemas.shop import OrderItem

item = await (
    OrderItem.async_queryset
    .select_related("order", "product")
    .filter_related(order__status="open", product__name__icontains="Widget")
    .get(id=1)
)
```

Related filters are preserved by `count()`, `update()`, and `delete()`, including
queries with only related filters. Counts and writes do not hydrate related
objects. Missing joined rows become `None`; use `__isnull=True` to match them.

## `prefetch_related(...)`

`prefetch_related()` runs the base query first, then executes additional filtered queries and attaches child collections to each base object.

```python
from fastpg import Prefetch, ReturnType

rows = await (
    Location.async_queryset
    .prefetch_related(
        Prefetch(
            "employees",
            Employee.async_queryset.filter(salary__gt=50000),
        )
    )
    .get(id=1)
    .return_as(ReturnType.DICT)
)
```

Requirements:

- The prefetched queryset model must define `Meta.relations` with a `Relation(...)`
  back to the base model. A mapping without a matching relation raises `InvalidPrefetchError`.
- The parent ID and child foreign-key fields must be included when selecting partial columns.
- Use an unambiguous relation back to the parent. When a child has multiple
  relations to the same parent model, the current implementation chooses the last
  matching entry in `Meta.relations`.

Behavior:

- For model-instance results, FastPG sets an attribute named by `dataset_name`.
- For `ReturnType.DICT`, FastPG inserts a new key with that dataset name.
- `select_related()` and `prefetch_related()` can be combined on the same queryset.
- Prefetching copies the supplied child queryset before adding parent IDs, so it
  can be reused across pages without accumulating constraints from earlier pages.
- A limit on the child queryset applies to the whole child query, not separately
  to each parent. Parent and child querysets select their read connections independently.

## Choosing a Strategy

- Use `select_related` for many-to-one or one-to-one style joins.
- Use `prefetch_related` for one-to-many child collections.
