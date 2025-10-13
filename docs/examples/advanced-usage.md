# Advanced usage

This example showcases several features working together: relations, complex
filters, JSON updates, and raw SQL pagination.

```python
from datetime import datetime, timedelta
from fastpg import (
    DatabaseModel,
    Relation,
    Q,
    ReturnType,
    AsyncPaginator,
    RawQueryAsyncPaginator,
)

class LineItem(DatabaseModel):
    id: int | None = None
    order_id: int
    sku: str
    quantity: int

    class Meta:
        db_table = "order_items"
        auto_generated_fields = ["id"]

class Order(DatabaseModel):
    id: int | None = None
    customer_id: int
    total: float
    metadata: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Meta:
        db_table = "orders"
        auto_generated_fields = ["id"]
        auto_now_add_fields = ["created_at"]
        auto_now_fields = ["updated_at"]
        relations = {
            "items": Relation(LineItem, base_field="id", foreign_field="order_id")
        }

# Complex filtering with Q objects
window_start = datetime.utcnow() - timedelta(days=30)
orders = await (
    Order.async_queryset
    .filter(
        Q(total__gte=100) | Q(metadata__jsonb_set__status__str="priority"),
        created_at__gte=window_start,
    )
    .select_related("items")
)

# Update JSON metadata
await (
    Order.async_queryset
    .filter(id=orders[0].id)
    .update(metadata__jsonb={"status": "processed"})
)

# Return as dictionaries for serialization
order_dicts = await (
    Order.async_queryset
    .filter(id__in=[order.id for order in orders])
    .return_as(ReturnType.DICT)
)

# Paginate orders for a dashboard
queryset = Order.async_queryset.order_by(created_at="DESC")
paginator = AsyncPaginator(page_size=25, queryset=queryset)
first_page = await paginator.get_page(1)

# Paginate with a raw SQL report
report_sql = """
SELECT customer_id, sum(total) AS revenue
FROM orders
WHERE created_at >= :start
GROUP BY customer_id
ORDER BY revenue DESC
LIMIT {limit} OFFSET {offset}
"""
report = RawQueryAsyncPaginator(
    page_size=20,
    query=report_sql,
    values={"start": window_start},
)
page = await report.get_page(1)
```

The example combines eager loading, advanced filtering, JSON updates, pagination,
and raw SQL to illustrate how FastPG supports both high-level and low-level
workflows.
