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


class Employee(DatabaseModel):
    id: int
    department_id: int | None = None
    name: str

    class Meta:
        db_table = "employees"
        primary_key = "id"
        relations = {
            "department": Relation(Department, foreign_field="department_id"),
        }
```

`foreign_field` is the column on the base model. FastPG renders the join as:

```sql
t.department_id = r.id
```

If you omit `related_name`, FastPG derives one from the related model class name in snake case.

## `select_related(...)`

`select_related()` performs a `LEFT JOIN` and hydrates one related object per base row.

```python
employee = await Employee.async_queryset.select_related("department").get(id=1)
```

Current behavior:

- Only one relation is used.
- If multiple names are passed, FastPG uses the first one.
- Missing relation names raise `InvalidRelatedFieldError`.

## `filter_related(...)`

Use `filter_related()` after `select_related()` to add `WHERE` conditions against the joined table:

```python
from fastpg import OrderBy

rows = await (
    Employee.async_queryset
    .select_related("department")
    .filter(salary__gte=50000)
    .filter_related(department__name="Engineering")
    .order_by(salary=OrderBy.DESCENDING)
)
```

Related-field filters use the relation name as the prefix, for example `department__name=...`.

## `prefetch_related(...)`

`prefetch_related()` runs the base query first, then executes additional filtered queries and attaches child collections to each base object.

```python
from fastpg import Prefetch, ReturnType

rows = await (
    Department.async_queryset
    .prefetch_related(Prefetch("employees", Employee.async_queryset.all()))
    .all()
    .return_as(ReturnType.DICT)
)
```

Requirements:

- The prefetched queryset model must define a `Relation(...)` back to the base model.
- Otherwise FastPG raises `InvalidPrefetchError`.

Behavior:

- For model-instance results, FastPG sets an attribute named by `dataset_name`.
- For `ReturnType.DICT`, FastPG inserts a new key with that dataset name.

## Choosing a Strategy

- Use `select_related` for many-to-one or one-to-one style joins.
- Use `prefetch_related` for one-to-many child collections.
