# Relationships

FastPG keeps relationship mapping simple: declare the join metadata yourself and
let `AsyncQuerySet` handle the SQL. This approach avoids heavy ORM abstractions
while still enabling eager loading.

## Defining relations

Use the `Relation` helper in a model's `Meta.relations` dictionary. Each entry
maps an attribute name to a `Relation` describing the related model and the join
keys.

```python
from fastpg import DatabaseModel, Relation

class OrderItem(DatabaseModel):
    id: int | None = None
    order_id: int
    sku: str

    class Meta:
        db_table = "order_items"
        primary_key = "id"

class Order(DatabaseModel):
    id: int | None = None
    customer_id: int
    total: float

    class Meta:
        db_table = "orders"
        primary_key = "id"
        relations = {
            "items": Relation(
                related_model=OrderItem,
                base_field="id",
                foreign_field="order_id",
                related_data_set_name="items",
            )
        }
```

The `related_data_set_name` controls which attribute on the parent model will
store the related records. If omitted, FastPG uses `<model name>_set`.

## Fetching related rows

Call `select_related` to join the related table and hydrate the nested models.

```python
order = await (
    Order.async_queryset
    .select_related("items")
    .get(id=1)
)

for item in order.items:
    print(item.sku)
```

`select_related` works with any queryset method (`get`, `filter`, `all`). When
you need to restrict the related rows, chain `filter_related` after
`select_related`.

```python
open_orders = await (
    Order.async_queryset
    .select_related("items")
    .filter(customer_id=customer_id)
    .filter_related(items__sku__startswith="SKU-")
)
```

The related queryset accepts the same lookup expressions as the primary
queryset. Prefix related fields with `<relation_name>__`.

## Working with the results

FastPG de-duplicates the main records before constructing model instances. Each
parent object receives a list of fully instantiated related models. If no rows
are found on the right side of the join, the list is empty.

Because the models are normal Pydantic instances you can serialise them using
`.model_dump()` or pass them straight to FastAPI responses.
