# Relationships

FastPG keeps relationship mapping simple: declare the join metadata yourself and
let `AsyncQuerySet` handle the SQL. This approach avoids heavy ORM abstractions
while still enabling eager loading.

## Defining relations

Use the `Relation` helper in a model's `Meta.relations` dictionary. Each entry
maps an attribute name to a `Relation` describing the related model and the join
keys. The shop demo bundles these patterns together for employees that belong to
departments.

```python
from fastpg import DatabaseModel, Relation


class Department(DatabaseModel):
    id: int | None = None
    name: str
    location: str

    class Meta:
        db_table = "departments"
        primary_key = "id"
        auto_generated_fields = ["id"]


class Employee(DatabaseModel):
    id: int | None = None
    department_id: int | None
    name: str
    email: str
    salary: float

    class Meta:
        db_table = "employees"
        primary_key = "id"
        auto_generated_fields = ["id"]
        relations = {
            "department": Relation(
                Department,
                base_field="department_id",
                foreign_field="id",
            )
        }
```

The `Relation` definition instructs FastPG how to join the two tables. When the
relation name matches the attribute you want on the model (`department` in this
case) you can skip `related_data_set_name`; FastPG uses the relation key by
default.

## Fetching related rows

Call `select_related` to join the related table and hydrate the nested models.
In the FastAPI demo endpoint we retrieve department data alongside employees and
filter on both the base and related models:

```python
from fastapi import APIRouter
from fastpg import OrderBy


router = APIRouter()


@router.get("/employees")
async def get_employees(department: str | None = None, salary: float | None = None):
    employees = Employee.async_queryset.select_related("department").all()
    if salary:
        employees = employees.filter(salary__gte=salary)
    if department:
        employees = employees.filter_related(department__name=department)
    return await employees.order_by(salary=OrderBy.DESCENDING)
```

`select_related` works with any queryset method (`get`, `filter`, `all`). When
you need to restrict the related rows, chain `filter_related` after
`select_related`. Related filters use the same lookup expressions as normal
filters, prefixed with `<relation_name>__`.

```python
sales_team = await (
    Employee.async_queryset
    .select_related("department")
    .filter_related(department__name__icontains="sales")
    .order_by(name=OrderBy.ASCENDING)
)
```

The related queryset accepts the same lookup expressions as the primary
queryset, enabling flexible joins without manual SQL.

## Working with the results

FastPG de-duplicates the main records before constructing model instances. Each
parent object receives a list of fully instantiated related models. If no rows
are found on the right side of the join, the list is empty.

Because the models are normal Pydantic instances you can serialise them using
`.model_dump()` or pass them straight to FastAPI responses.

## Prefetching child collections

When a parent model owns many children (orders with line items, departments with
employees) prefer `prefetch_related`. It executes the base query first and then
populates the collections with a second query per relation, keeping the SQL
readable and avoiding cartesian explosions.

```python
from fastpg import Prefetch, ReturnType


@router.get("/departments")
async def get_departments():
    departments = await Department.async_queryset.prefetch_related(
        Prefetch("employees", Employee.async_queryset.all())
    ).all().return_as(ReturnType.DICT)
    return departments
```

Each `Prefetch` requires the attribute name and a queryset that knows how to
fetch the related objects. FastPG matches records automatically by comparing the
primary key of the base objects (`id`) with the foreign key on the related ones
(`department_id` in this example).
