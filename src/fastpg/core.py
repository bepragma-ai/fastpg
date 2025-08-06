"""
Django-inspired lightweight ORM with Pydantic integration for seamless FastAPI support.


## Creating a Database Model
Decorate a Pydantic `BaseModel` class using `@db_model` to turn it into a fully functional DB model.
- Data queried from the database is instantiated as a Pydantic model (validation skipped assuming verified data).
- Models can be directly used as FastAPI input/output.
- Both synchronous and asynchronous APIs are supported.
```python
from fastpg import db_model
from pydantic import BaseModel
from datetime import datetime

@db_model
class Customer(BaseModel):
    id: int | None = None
    first_name: str
    last_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Meta:
        db_table = 'task_checklists_customer'
        primary_key = 'id'
        auto_generated_fields = ['id']
        auto_now_add_fields = ['created_at']
        auto_now_fields = ['updated_at']
```

#### Saving Models
```python
# Async example
customer = await Customer.async_queryset.get(id=10)
customer.first_name = 'Jane'
await customer.async_save()
```

#### Usage in FastAPI
```python
# Async example
customer = await Customer.async_queryset.get(id=10)
customer.first_name = 'Jane'
await customer.async_save()s
```


## QuerySets
Models provide two query interfaces:
- `async_queryset` — for async DB access
- `sync_query_set` — for sync DB access

#### Query Methods
- `get(**kwargs)`: Fetch a single item. Raises `DoesNotExist` if no result is found.
- `filter(**kwargs)`: Fetch multiple results. Returns empty list if no matches.
- `count(**kwargs)`: Returns the count of rows matching given filters.
- `create(**kwargs)`: Inserts a new record and returns the created model instance.
- `bulk_update(filters: dict, updates: dict)`: Updates all matching rows based on filters.

## Filter Syntax
The ORM supports expressive filtering using field-based keyword arguments, inspired by Django's syntax. Filters can be combined to create complex queries. Here’s how each type works:

1. Equality Filter `field=value`: This performs a standard SQL equality check: `WHERE first_name = 'Alice'`. Example: `.get(first_name='Alice')`
2. Comparison Filters: You can use special suffixes with `__` to express SQL comparison operators.
    - Supported Operators:
        - `field__gt=value` → `field > value`
        - `field__lt=value` → `field < value`
        - `field__gte=value` → `field >= value`
        - `field__lte=value` → `field <= value`
        - `field__ne=value` → `field != value`
        - `field__is_null=True/False` → `field IS NULL` or `field IS NOT NULL`
    - Example: `age__gt=25, created_at__lte=datetime.utcnow()` translates to `WHERE age > 25 AND created_at <= now()`
3. IN Clause `field__in=[...]`: Translates to `WHERE id IN (1, 2, 3)`
    > ⚠️ NOTE: The value must be a list; otherwise, an InvalidINClauseValueError is raised.
4. OR Conditions `__or=[{condition1}, {condition2}, ...]`: The following example
    ```python
    __or=[
        {"first_name": "John"},
        {"age__lt": 18}
    ]
    ```
    Translates to
    ```sql
    WHERE (first_name = 'John' OR age < 18)
    ```
    You can also combine __or with other filters:
    ```python
    await Customer.async_queryset.filter(
        last_name="Doe",
        __or=[
            {"id__gt": 5},
            {"first_name": "Jane"}
        ]
    )
    ```
    Which translates to
    ```sql
    WHERE last_name = 'Doe' AND (id > 5 OR first_name = 'Jane')
    ```
5. Additional filter options:
    - `columns={'id', 'first_name'}` — Select specific columns by providing them as a set of string
    - `order_by={'created_at': OrderBy.DESCENDING}` — Order data by providing dict of column names. `OrderBy` can be imported from `from fastpg import OrderBy`
    - `self.fetch_limit=10`
    - `self.fetch_offset=20`

## Error Handling
Common exceptions:
- `DoesNotExist` — When get() finds no record
- `UnsupportedOperatorError` — If filter uses an unknown operator
- `InvalidINClauseValueError` — If __in receives non-list value
- `DatabaseError` — For any underlying SQL/connection error


## Notes
- `async_save()` method updates the row based on the primary key.
- During insertions, fields listed in `BaseModel.Meta.auto_generated_fields` are excluded.
- `model_construct(**record)` is used for faster instantiation without validation during reads.
"""

from functools import reduce
from typing import Any, ClassVar, Dict
from typing_extensions import Self
from pydantic import BaseModel

from databases.backends.common.records import Record

from .constants import (
    ReturnTypes,
    OnConflict,
)

from .utils import (
    Relation,
    Q,
)

from .preprocessors import (
    PreCreateProcessors,
    PreSaveProcessors,
)

from .db import (
    ASYNC_CUSTOMERS_DB_READ,
    ASYNC_CUSTOMERS_DB_WRITE,
)

from .errors import (
    MalformedMetaError,
    MalformedQuerysetError,
    DatabaseError,
    DuplicateKeyDatabaseError,
    UnsupportedOperatorError,
    DoesNotExist,
    MultipleRecordsFound,
    NothingToCreateError,
    UnrestrictedUpdateError,
    UnrestrictedDeleteError,
)

from .print import print_red


class AsyncQuerySet:
    """Build and execute database queries for a model."""

    def __init__(self, model) -> None:
        self.Model = model
        self.ModelMeta = self.Model.Meta
        try:
            self.table = self.ModelMeta.db_table
        except AttributeError as e:
            if str(e) == 'Meta':
                raise MalformedMetaError(self.Model.__name__)
        self.model_fields = self.Model.__fields__.keys()

        self.columns_to_fetch = self.model_fields
        self.where_conditions = None
        self.fetch_limit = None
        self.fetch_offset = None
        self.order_by_fields = None

        self.action = None
        self.base_query = None
        self.query = None
        self.query_param_values = {}
        self.query_executed = False
        self.records = None

        self.fetch_related = False
        self.relation:Relation = None

        self.update_clause = None

        self.return_type = ReturnTypes.MODEL_INSTANCE

    def _reduce_conditions(self, *args, **kwargs) -> Q:
        conditions = []
        if kwargs:
            conditions.append(Q(**kwargs))
        if args:
            conditions.extend(args)
        return reduce(lambda x, y: x & y, conditions)

    def _denormalize_data(self) -> list[dict]:
        items = {}
        for record in self.records:
            left_id_val = record[f't_{self.relation.base_field}']
            if left_id_val not in items:
                items[left_id_val] = {f: record[f't_{f}'] for f in self.columns_to_fetch}
                items[left_id_val][self.relation.related_data_set_name] = []
            
            if record[f'r_{self.relation.foreign_field}']:
                items[left_id_val][self.relation.related_data_set_name].append(
                    {f: record[f'r_{f}'] for f in self.relation.model_fields})

        return [items[key] for key in items.keys()]

    def _serialize_data(self) -> None:
        if self.action == 'count':
            return

        if self.return_type == ReturnTypes.MODEL_INSTANCE:
            self.records = [self.Model.model_construct(**record) for record in self.records]

    async def _execute_query(self, func) -> None:
        self.query = f'{self.base_query} WHERE {self.where_conditions}' if self.where_conditions else self.base_query

        if self.order_by_fields:
            self.query += ' ORDER BY ' + ','.join(f'{k} {v}' for k, v in self.order_by_fields.items())
        if self.fetch_limit:
            self.query += f' LIMIT {self.fetch_limit}'
        if self.fetch_offset:
            self.query += f' OFFSET {self.fetch_offset}'
        
        try:
            self.records = await ASYNC_CUSTOMERS_DB_READ.fetch_all(
                query=self.query, values=self.query_param_values)
            self.query_executed = True
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))
        
        self.records = [record._mapping for record in self.records]
        self._serialize_data()
        return func()

    async def _execute_query_with_select_related(self, func) -> None:
        main_table_fields = ','.join(f't.{f} AS t_{f}' for f in self.columns_to_fetch)
        related_table_fields = ','.join(f'r.{f} AS r_{f}' for f in self.relation.model_fields)

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        if self.where_conditions:
            inner_query = f'SELECT {columns_to_fetch} FROM {self.table} WHERE {self.where_conditions}'
        else:
            inner_query = f'SELECT {columns_to_fetch} FROM {self.table}'

        self.query = f"""
            WITH main_table AS (
                {inner_query}
            )
            SELECT {main_table_fields}, {related_table_fields}
            FROM main_table t
            LEFT JOIN {self.relation.table} r ON {self.relation.render_on_clause()}"""

        if self.order_by_fields:
            # self.query += ' ORDER BY ' + ','.join(f't.{k} {v}' for k, v in self.order_by_fields.items())

            _related_name = self.relation.related_data_set_name
            _clauses = []
            for k, v in self.order_by_fields.items():
                if f'{_related_name}__' in k:
                    k = k.replace(f'{_related_name}__', '')
                    _clauses.append(f'r.{k} {v}')
                else:
                    _clauses.append(f't.{k} {v}')
            self.query += ' ORDER BY ' + ','.join(_clauses)
        if self.fetch_limit:
            self.query += f' LIMIT {self.fetch_limit}'
        if self.fetch_offset:
            self.query += f' OFFSET {self.fetch_offset}'

        try:
            self.records = await ASYNC_CUSTOMERS_DB_READ.fetch_all(
                query=self.query, values=self.query_param_values)
            self.query_executed = True
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))

        self.records = [record._mapping for record in self.records]
        self.records = self._denormalize_data()
        self.return_type = ReturnTypes.DICT
        self._serialize_data()
        return func()

    async def execute_raw_query(self, query:str, values:Dict[str, Any]):
        self.query = query
        self.query_param_values = values
        
        try:
            self.records = await ASYNC_CUSTOMERS_DB_READ.fetch_all(
                query=self.query, values=self.query_param_values)
            self.query_executed = True
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))
        
        self.records = [record._mapping for record in self.records]
        self._serialize_data()
        return self.records

    def columns(self, *columns:set[str]) -> Self:
        self.columns_to_fetch = list(columns)
        return self

    def get(self, *args, **kwargs) -> Self:
        """Fetch a single record matching the given conditions."""
        self.action = 'get'

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table}'

        conditions = self._reduce_conditions(*args, **kwargs)
        self.where_conditions = conditions.where_clause
        self.query_param_values = conditions.params

        return self

    def _get(self):
        record_count = len(self.records)
        if record_count == 1:
            return self.records[0]
        elif record_count == 0:
            raise DoesNotExist(model_name=self.Model.__name__, query=self.query)
        else:
            raise MultipleRecordsFound(model_name=self.Model.__name__, query=self.query)

    def filter(self, *args, **kwargs) -> Self:
        """Filter records based on provided conditions."""
        self.action = 'filter'

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table}'

        conditions = self._reduce_conditions(*args, **kwargs)
        self.where_conditions = conditions.where_clause
        self.query_param_values = conditions.params

        return self

    def _filter(self):
        return self.records

    def all(self) -> Self:
        """Select all records for the model."""
        self.action = 'all'

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table}'

        self.where_conditions = None
        self.query_param_values = None
        return self

    def _all(self):
        return self.records

    def count(self) -> Self:
        """Count the number of records matching the query."""
        self.action = 'count'
        self.fetch_related = False
        self.base_query = f'SELECT count({self.ModelMeta.primary_key}) FROM {self.table}'
        return self

    def _count(self) -> int:
        record_count = len(self.records)
        if record_count == 1:
            return self.records[0]['count']

    def select_related(self, *relation_names:list[str]) -> Self:
        self.fetch_related = True
        self.relation = self.ModelMeta.relations[relation_names[0]]
        self.relation.set_related_data_set_name(relation_names[0])
        return self

    def limit(self, fetch_limit:int) -> Self:
        self.fetch_limit = fetch_limit
        return self

    def offset(self, fetch_offset:int) -> Self:
        self.fetch_offset = fetch_offset
        return self

    def order_by(self, **order_by:dict[str, str]) -> Self:
        self.order_by_fields = order_by
        return self

    async def create(
        self,
        # on_conflict:str=None,  # Options: None | "ignore" | "update"
        # conflict_target:list[str]=None,  # Required for "update"
        # update_fields:list[str]=None,    # Required for "update"
        **kwargs
    ):
        """
        await db.create(..., on_conflict=OnConflict.DO_NOTHING)
        await db.create(
            ...,
            on_conflict=OnConflict.UPDATE,
            conflict_target=["id"],  # usually a unique constraint
            update_fields=["name"]
        )
        """
        self.fetch_related = False
        primary_key_field = self.ModelMeta.primary_key
        model_obj = self.Model(**kwargs)
        PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)

        model_dict = model_obj.dict()
        PreCreateProcessors.model_dict_populate_auto_generated_fields(model_dict, self.Model)

        col_names = model_dict.keys()
        columns = ', '.join(col_names)
        placeholders = ', '.join(f':{col}' for col in col_names)

        # Base query
        query = f'INSERT INTO {self.table} ({columns}) VALUES ({placeholders})'

        # Add ON CONFLICT logic
        # if on_conflict == "ignore":
        #     query += " ON CONFLICT DO NOTHING"
        # elif on_conflict == "update":
        #     if not conflict_target or not update_fields:
        #         raise ValueError("conflict_target and update_fields must be provided for ON CONFLICT UPDATE.")
        #     target = ', '.join(conflict_target)
        #     updates = ', '.join(f"{field} = EXCLUDED.{field}" for field in update_fields)
        #     query += f" ON CONFLICT ({target}) DO UPDATE SET {updates}"

        query += f" RETURNING {primary_key_field} AS new_id"

        try:
            new_id = await ASYNC_CUSTOMERS_DB_WRITE.execute(
                query=query, values=model_dict)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            if sqlstate == '23505':
                raise DuplicateKeyDatabaseError(
                    table_name=self.table,
                    sqlstate=sqlstate,
                    message=str(e))
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
        
        setattr(model_obj, primary_key_field, new_id)
        return model_obj

    async def bulk_create(
        self,
        values:list[dict],
        skip_validations:bool=False,
        on_conflict:str=None,
        conflict_target:list[str]=None,  # Required for "update"
        update_fields:list[str]=None     # Required for "update"
    ):
        """
        await db.bulk_create(values=payload, on_conflict=OnConflict.DO_NOTHING)
        await db.bulk_create(
            values=payload,
            on_conflict=OnConflict.UPDATE,
            conflict_target=["id"],  # or other unique constraint
            update_fields=["name", "email"]
        )
        """
        if len(values) == 0:
            raise NothingToCreateError()

        self.fetch_related = False
        model_objs = []
        model_dicts = []

        if skip_validations:
            for item in values:
                model_obj = self.Model.model_construct(**item)
                PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)
                model_objs.append(model_obj)
        else:
            for item in values:
                model_obj = self.Model(**item)
                PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)
                model_objs.append(model_obj)

        for model_obj in model_objs:
            model_dict = model_obj.dict()
            PreCreateProcessors.model_dict_populate_auto_generated_fields(model_dict, self.Model)
            model_dicts.append(model_dict)

        col_names = model_dicts[0].keys()
        columns = ', '.join(col_names)
        placeholders = ', '.join(f':{col}' for col in col_names)

        # Base insert
        query = f'INSERT INTO {self.table} ({columns}) VALUES ({placeholders})'

        # Add ON CONFLICT clause
        if on_conflict == OnConflict.DO_NOTHING:
            query += " ON CONFLICT DO NOTHING"
        elif on_conflict == OnConflict.UPDATE:
            if not conflict_target or not update_fields:
                raise ValueError("conflict_target and update_fields must be provided for ON CONFLICT UPDATE.")
            target = ', '.join(conflict_target)
            updates = ', '.join(f"{field} = EXCLUDED.{field}" for field in update_fields)
            query += f" ON CONFLICT ({target}) DO UPDATE SET {updates}"

        try:
            await ASYNC_CUSTOMERS_DB_WRITE.execute_many(
                query=query, list_of_values=model_dicts)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            if sqlstate == '23505':
                raise DuplicateKeyDatabaseError(
                    table_name=self.table,
                    sqlstate=sqlstate,
                    message=str(e))
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))

    async def get_or_create(self, defaults:dict[str, Any], **kwargs):
        self.fetch_related = False
        created = False
        try:
            obj = await self.get(**kwargs)
        except DoesNotExist:
            data = {**kwargs, **defaults}
            obj = await self.create(**data)
            created = True
        return obj, created

    def update(self, **kwargs) -> Self:
        """Update records matching the query with provided values."""
        if self.where_conditions is None:
            raise UnrestrictedUpdateError()
        
        self.action = 'update'
        self.fetch_related = False
        _update_clause = []
        for key in kwargs.keys():
            if "__" in key:
                field, op = key.split("__", 1)
                if op == 'add':
                    _update_clause.append(f'{field}={field} + {kwargs[key]}')
                elif op == 'sub':
                    _update_clause.append(f'{field}={field} - {kwargs[key]}')
                elif op == 'mul':
                    _update_clause.append(f'{field}={field} * {kwargs[key]}')
                elif op == 'div':
                    _update_clause.append(f'{field}={field} / {kwargs[key]}')
                else:
                    raise UnsupportedOperatorError(message=f'Invalid operation "{op}" in update')
            else:
                _update_clause.append(f'{key}=:set_{key}')
                self.query_param_values[f'set_{key}'] = kwargs[key]

        self.update_clause = ', '.join(_update_clause)

        return self

    async def _update(self) -> int:
        if not self.query_executed:
            self.query = f'''
                WITH updated AS (
                    UPDATE {self.table}
                    SET {self.update_clause}
                    WHERE {self.where_conditions}
                    RETURNING {self.ModelMeta.primary_key} AS updated_id
                ) SELECT COUNT(*) AS updated_count FROM updated;'''
            
            try:
                self.records = await ASYNC_CUSTOMERS_DB_READ.execute(
                    query=self.query, values=self.query_param_values)
                self.query_executed = True
            except Exception as e:
                print_red(e)
                raise DatabaseError(
                    name=type(e).__name__,
                    sqlstate=e.sqlstate,
                    message=str(e))

        return self.records

    def delete(self) -> Self:
        """Delete records matching the query."""
        if self.where_conditions is None:
            raise UnrestrictedDeleteError()

        self.action = 'delete'
        self.fetch_related = False
        return self

    async def _delete(self) -> int:
        if not self.query_executed:
            self.query = f'''
                WITH deleted AS (
                    DELETE FROM {self.table}
                    WHERE {self.where_conditions}
                    RETURNING {self.ModelMeta.primary_key} AS deleted_id
                ) SELECT COUNT(*) AS deleted_count FROM deleted;'''

            try:
                self.records = await ASYNC_CUSTOMERS_DB_READ.execute(
                    query=self.query, values=self.query_param_values)
                self.query_executed = True
            except Exception as e:
                raise DatabaseError(
                    name=type(e).__name__,
                    sqlstate=e.sqlstate,
                    message=str(e))

        return self.records

    def return_as(self, return_type:str) -> Self:
        self.return_type = return_type
        return self

    def __await__(self):
        if self.action == 'update':
            return self._update().__await__()
        elif self.action == 'delete':
            return self._delete().__await__()
        elif self.action == 'get':
            func = self._get
        elif self.action == 'filter':
            func = self._filter
        elif self.action == 'all':
            func = self._all
        elif self.action == 'count':
            func = self._count
        else:
            raise MalformedQuerysetError(self.Model.__name__)

        if not self.query_executed:
            if self.fetch_related:
                return self._execute_query_with_select_related(func).__await__()
            else:
                return self._execute_query(func).__await__()


class AsyncRawQuery:

    def __init__(self, query:str, values:dict[str, Any]):
        self.query = query
        self.values = values

    async def fetch(self) -> list[Record]:
        try:
            records = await ASYNC_CUSTOMERS_DB_READ.fetch_all(
                query=self.query, values=self.values)
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))
        return [dict(record) for record in records]


class classproperty:
    """Descriptor that works like @property but for classes."""
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner_cls):
        return self.func(owner_cls)
        

class DatabaseModel(BaseModel):
    async_queryset:ClassVar[AsyncQuerySet]
    
    @classproperty
    def async_queryset(cls):
        return AsyncQuerySet(model=cls)
    
    async def async_save(self, columns:list[str]=None) -> bool:
        PreSaveProcessors.model_obj_populate_auto_now_fields(self)

        values = {}
        model_dict = self.dict()

        if columns is None:
            columns = model_dict.keys()

        for col in columns:
            values[col] = model_dict[col]

        set_clause = ', '.join(f'{col}=:{col}' for col in columns)
        where_clause = f'{self.Meta.primary_key} = :{self.Meta.primary_key}'
        values[self.Meta.primary_key] = model_dict[self.Meta.primary_key]

        query = f'UPDATE {self.Meta.db_table} SET {set_clause} WHERE {where_clause} RETURNING 1'

        try:
            updated = await ASYNC_CUSTOMERS_DB_WRITE.execute(
                query=query, values=values)
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))

        return bool(updated)

    async def async_delete(self) -> bool:
        model_dict = self.dict()
        values = {}
        for key in model_dict.keys():
            if key == self.Meta.primary_key:
                values[key] = model_dict[key]
                break

        where_clause = f'{self.Meta.primary_key} = :{self.Meta.primary_key}'
        query = f'''
            WITH deleted AS (
                DELETE FROM {self.Meta.db_table}
                WHERE {where_clause}
                RETURNING {self.Meta.primary_key} AS deleted_id
            ) SELECT COUNT(*) AS deleted_count FROM deleted;'''

        try:
            deleted_count = await ASYNC_CUSTOMERS_DB_WRITE.execute(
                query=query, values=values)
        except Exception as e:
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=e.sqlstate,
                message=str(e))
        
        return bool(deleted_count)
