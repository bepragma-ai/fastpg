# Relationships

FastPG relationships are explicit and lightweight.

## Define a relation

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

`foreign_field` is the field on the base model table (`t.foreign_field = r.related_id_field`).

## `select_related(...)`

Performs a left join and hydrates one related object per base row.

```python
employee = await Employee.async_queryset.select_related("department").get(id=1)
```

Current implementation uses the first relation name passed to `select_related(...)`.

Use `filter_related(...)` to filter related table columns:

```python
rows = await (
    Employee.async_queryset
    .select_related("department")
    .filter_related(department__name="Engineering")
    .all()
)
```

## `prefetch_related(...)`

Loads child collections in a second query and attaches them to each base object.

```python
from fastpg import Prefetch, ReturnType

rows = await (
    Department.async_queryset
    .prefetch_related(Prefetch("employees", Employee.async_queryset.all()))
    .all()
    .return_as(ReturnType.DICT)
)
```

Requirements for prefetch:

- Prefetch queryset model must define a relation that points back to the base model.
- Otherwise FastPG raises `InvalidPrefetchError`.

## Choosing strategy

- Use `select_related` for one-to-one or many-to-one style joins.
- Use `prefetch_related` for one-to-many collections.
