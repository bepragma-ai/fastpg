from __future__ import annotations
from functools import reduce
from copy import copy
from typing import Optional, Any, ClassVar, Dict, List
from typing_extensions import Self
import json

from pydantic import BaseModel, ConfigDict, PrivateAttr

from databases.backends.common.records import Record

from .constants import (
    ReturnType,
    OnConflict,
    OrderBy,
    RENDER_UPDATE_SUFFIXES,
    QueryAction,
)

from .utils import (
    Relation,
    Prefetch,
    Q,
    InClauseParam,
)

from .fields import CustomJsonEncoder

from .db import AsyncPostgresDBConnection

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
    InvalidRelatedFieldError,
    InvalidPrefetchError,
    InvalidDatabaseModelUriError,
)

from .preprocessors import (
    PreCreateProcessors,
    PreSaveProcessors,
)

from .fastpg import get_fastpg


_FASTPG_MODELS:Dict[str, type["DatabaseModel"]] = {}
def get_database_model_by_uri(uri:str) -> type["DatabaseModel"]:
    try:
        return _FASTPG_MODELS[uri]
    except KeyError:
        raise InvalidDatabaseModelUriError(uri, list(_FASTPG_MODELS.keys()))


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
        self.model_fields = self.Model.model_fields.keys()
        self.columns_to_fetch:List[str] = self.model_fields

        self.action:QueryAction = QueryAction.NONE
        self.base_query:str = ''
        self.query:str = ''
        self.query_executed = False

        self.conditions = []
        self.where_conditions:str = ''
        self.query_param_values = {}
        self.related_conditions = []
        self.related_where_conditions:str = ''
        self.related_query_param_values = {}

        self.fetch_limit:Optional[int] = None
        self.fetch_offset:Optional[int] = None
        self.order_by_fields:Optional[Dict[str, OrderBy]] = None

        self.records = None

        self.run_select_related:bool = False
        self.relations:List[Relation] = []
        
        self.run_prefetch_related:bool = False
        self.prefetches:List[Prefetch] = []

        self.run_lock_for_update:bool = False

        self.update_clause:Optional[str] = None
        self.update_param_values = {}

        self.return_type = ReturnType.MODEL_INSTANCE

        fastpg = get_fastpg()
        self.read_connection = fastpg.db_conn_manager.db_for_read()
        self.write_connection = fastpg.db_conn_manager.db_for_write()

    def _invalidate(self) -> None:
        self.query_executed = False
        self.records = None

    def _validate_columns(self, columns) -> None:
        for column in columns:
            if column not in self.model_fields:
                raise ValueError(f'Unknown field on {self.Model.__name__}: {column}')

    def _model_instance(self, record, model=None):
        obj = (model or self.Model)(**record)
        obj._write_connection = self.write_connection
        return obj

    def _joins(self) -> str:
        joins = []
        for index, relation in enumerate(self.relations):
            alias = 'r' if index == 0 else f'r{index}'
            joins.append(
                f'LEFT JOIN {relation.table} {alias} '
                f'ON t.{relation.foreign_field} = {alias}.{relation.related_id_field}'
            )
        return ' '.join(joins)

    def _query_conditions(self):
        where = self.where_conditions
        if self.related_where_conditions:
            # Keep related predicates when the outer operation does not load joins.
            related = (
                f't.{self.ModelMeta.primary_key} IN ('
                f'SELECT t.{self.ModelMeta.primary_key} FROM {self.table} t {self._joins()} '
                f'WHERE {self.related_where_conditions})'
            )
            where = f'({where}) AND ({related})' if where else related
        return where, {**self.query_param_values, **self.related_query_param_values}

    def _reduce_conditions(self, *args, **kwargs) -> Q:
        if kwargs:
            self.conditions.append(Q(**kwargs))
        if args:
            self.conditions.extend(args)
        return reduce(lambda x, y: x & y, self.conditions) if self.conditions else Q()
    
    def _reduce_related_conditions(self, *args, **kwargs) -> Q:
        if kwargs:
            relation_aliases = {
                relation.related_name: 'r' if index == 0 else f'r{index}'
                for index, relation in enumerate(self.relations)
            }
            self.related_conditions.append(Q(relation_aliases=relation_aliases, **kwargs))
        if args:
            self.related_conditions.extend(args)
        return reduce(lambda x, y: x & y, self.related_conditions) if self.related_conditions else Q()

    def _denormalize_related_data(self) -> list[dict]:
        items = []
        for record in self.records:
            item = {f: record[f't_{f}'] for f in self.columns_to_fetch}
            for index, relation in enumerate(self.relations):
                alias = 'r' if index == 0 else f'r{index}'
                item[relation.related_name] = None
                if record[f'{alias}_{relation.related_id_field}'] is not None:
                    item[relation.related_name] = {
                        f: record[f'{alias}_{f}'] for f in relation.model_fields
                    }
            
            items.append(item)
        return items

    def _serialize_data(self) -> None:
        if self.action == QueryAction.COUNT:
            return

        if self.return_type == ReturnType.MODEL_INSTANCE:
            if self.run_select_related:
                model_objs = []
                for record in self.records:
                    model_obj = self._model_instance(record)
                    for relation in self.relations:
                        related_record = record[relation.related_name]
                        related_obj = self._model_instance(related_record, relation.RelatedModel) if related_record else None
                        setattr(model_obj, relation.related_name, related_obj)
                    model_objs.append(model_obj)
                self.records = model_objs
            else:
                self.records = [self._model_instance(record) for record in self.records]
        else:
            # Return as list of dict
            self.records = [{**record} for record in self.records]

    async def _execute_query(self, func) -> None:
        where, values = self._query_conditions()
        if self.action != QueryAction.COUNT:
            self.base_query = f'SELECT {",".join(self.columns_to_fetch)} FROM {self.table} t'
        self.query = f'{self.base_query} WHERE {where}' if where else self.base_query

        if self.run_lock_for_update:
            _connection = self.write_connection
            self.query += ' FOR UPDATE'
        
        else:
            _connection = self.read_connection
            if self.order_by_fields and self.action != QueryAction.COUNT:
                self.query += ' ORDER BY ' + ','.join(f'{k} {v}' for k, v in self.order_by_fields.items())
            if self.fetch_limit is not None and self.action != QueryAction.COUNT:
                self.query += f' LIMIT {self.fetch_limit}'
            if self.fetch_offset and self.action != QueryAction.COUNT:
                self.query += f' OFFSET {self.fetch_offset}'

        try:
            self.records = await _connection.fetch_all(
                query=self.query, values=values)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
        self._serialize_data()
        return func()

    async def _execute_query_with_select_related(self, func) -> None:
        main_table_fields = ','.join(f't.{f} AS t_{f}' for f in self.columns_to_fetch)
        related_table_fields = []
        for index, relation in enumerate(self.relations):
            alias = 'r' if index == 0 else f'r{index}'
            related_table_fields.extend(
                f'{alias}.{f} AS {alias}_{f}' for f in relation.model_fields
            )

        self.query = f"""
            SELECT {main_table_fields}, {','.join(related_table_fields)}
            FROM {self.table} t {self._joins()}
        """
        if self.where_conditions:
            self.query += f'WHERE ({self.where_conditions})'
            if self.related_where_conditions:
                self.query += f' AND ({self.related_where_conditions})'
        else:
            if self.related_where_conditions:
                self.query += f' WHERE {self.related_where_conditions}'
        if self.order_by_fields:
            _clauses = []
            for k, v in self.order_by_fields.items():
                _clauses.append(f't.{k} {v}')
            self.query += ' ORDER BY ' + ','.join(_clauses)
        if self.fetch_limit is not None:
            self.query += f' LIMIT {self.fetch_limit}'
        if self.fetch_offset:
            self.query += f' OFFSET {self.fetch_offset}'

        connection = self.write_connection if self.run_lock_for_update else self.read_connection
        if self.run_lock_for_update:
            self.query += ' FOR UPDATE OF t'

        try:
            self.records = await connection.fetch_all(
                query=self.query, values={
                    **self.query_param_values,
                    **self.related_query_param_values})
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))

        self.records = self._denormalize_related_data()
        self._serialize_data()
        return func()
    
    async def _execute_query_with_prefetch_related(self, func) -> None:
        if self.run_lock_for_update:
            model_name = self.Model.__name__
            raise MalformedQuerysetError(
                model_name, f'"{model_name}" queryset is invalid: prefetch_related cannot run when locked for update')

        if self.run_select_related:
            base_objs = await self._execute_query_with_select_related(func)
        else:
            base_objs = await self._execute_query(func)
        if not isinstance(base_objs, list):
            base_objs = [base_objs]
        
        if len(base_objs) == 0:
            return func()

        as_models = self.return_type == ReturnType.MODEL_INSTANCE
        get_value = getattr if as_models else lambda obj, field: obj[field]
        for prefetch in self.prefetches:
            # Each execution adds its own parent IDs without mutating the supplied queryset.
            queryset = copy(prefetch.queryset)
            queryset.conditions = list(queryset.conditions)
            ids = [get_value(obj, prefetch.id_field) for obj in base_objs]
            children = await queryset.filter(
                **{f'{prefetch.foreign_field}__in': ids}
            ).return_as(self.return_type)
            grouped = {}
            for child in children:
                grouped.setdefault(get_value(child, prefetch.foreign_field), []).append(child)
            for obj in base_objs:
                children = grouped.get(get_value(obj, prefetch.id_field), [])
                if as_models:
                    setattr(obj, prefetch.dataset_name, children)
                else:
                    obj[prefetch.dataset_name] = children

        return func()

    async def execute_raw_query(self, query:str, values:Dict[str, Any]):
        self.query = query
        self.query_param_values = values

        try:
            self.records = await self.read_connection.fetch_all(
                query=self.query, values=self.query_param_values)
            self.query_executed = True
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
        
        self._serialize_data()
        return self.records

    def using(self, conn_name:str) -> Self:
        self._invalidate()
        self.read_connection = get_fastpg().db_conn_manager.get_db_conn(conn_name)
        return self

    def columns(self, *columns:set[str]) -> Self:
        self._validate_columns(columns)
        self._invalidate()
        self.columns_to_fetch = list(columns)
        return self

    def get(self, *args, **kwargs) -> Self:
        """Fetch a single record matching the given conditions."""
        self._invalidate()
        self.action = QueryAction.GET

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table} t'

        all_conditions = self._reduce_conditions(*args, **kwargs)
        self.where_conditions = all_conditions.where_clause
        self.query_param_values = all_conditions.params

        return self

    def _get(self):
        record_count = len(self.records)
        if record_count == 1:
            return self.records[0]
        elif record_count == 0:
            raise DoesNotExist(model_name=self.Model.__name__, query=self.query)
        else:
            raise MultipleRecordsFound(model_name=self.Model.__name__, query=self.query)

    def filter_related(self, *args, **kwargs) -> Self:
        self._invalidate()
        all_conditions = self._reduce_related_conditions(*args, **kwargs)
        self.related_where_conditions = all_conditions.where_clause
        self.related_query_param_values = all_conditions.params

        return self

    def filter(self, *args, **kwargs) -> Self:
        """Filter records based on provided conditions."""
        self._invalidate()
        self.action = QueryAction.FILTER

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table} t'

        all_conditions = self._reduce_conditions(*args, **kwargs)
        self.where_conditions = all_conditions.where_clause
        self.query_param_values = all_conditions.params

        return self

    def _filter(self):
        return self.records

    def lock_for_update(self, *args, **kwargs) -> Self:
        """Lock rows for update based on provided conditions."""
        self._invalidate()
        self.run_lock_for_update = True
        return self

    def all(self) -> Self:
        """Select all records for the model."""
        self._invalidate()
        self.action = QueryAction.ALL

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table} t'

        self.where_conditions = ''
        self.query_param_values = {}
        self.conditions = []
        return self

    def _all(self):
        return self.records

    def count(self) -> Self:
        """Count the number of records matching the query."""
        self._invalidate()
        self.action = QueryAction.COUNT
        self.base_query = f'SELECT count({self.ModelMeta.primary_key}) FROM {self.table} t'
        return self

    def _count(self) -> int:
        record_count = len(self.records)
        if record_count == 1:
            return self.records[0]['count']

    def select_related(self, *relation_names:List[str]) -> Self:
        self._invalidate()
        self.run_select_related = True
        for relation_name in relation_names:
            try:
                relation = self.ModelMeta.relations[relation_name]
                if relation not in self.relations:
                    self.relations.append(relation)
            except KeyError:
                raise InvalidRelatedFieldError(self.Model.__name__, relation_name, self.ModelMeta.relations.keys())
        return self
    
    def prefetch_related(self, *prefetches:List[Prefetch]) -> Self:
        self._invalidate()
        self.run_prefetch_related = True
        self.prefetches = prefetches
        for prefetch in self.prefetches:
            relation_found = False
            for relation in prefetch.queryset.Model.Meta.relations.values():
                if relation.RelatedModel == self.Model:
                    relation_found = True
                    prefetch.set_foreign_field(relation.foreign_field)
                    prefetch.set_id_field(relation.related_id_field)
            if not relation_found:
                raise InvalidPrefetchError(self.Model.__name__, prefetch.queryset.Model.__name__)
        return self

    def limit(self, fetch_limit:int) -> Self:
        if type(fetch_limit) is not int or fetch_limit < 0:
            raise ValueError('limit must be a non-negative integer')
        self._invalidate()
        self.fetch_limit = fetch_limit
        return self

    def offset(self, fetch_offset:int) -> Self:
        if type(fetch_offset) is not int or fetch_offset < 0:
            raise ValueError('offset must be a non-negative integer')
        self._invalidate()
        self.fetch_offset = fetch_offset
        return self

    def order_by(self, **order_by) -> Self:
        self._validate_columns(order_by)
        if any(direction not in (OrderBy.ASCENDING, OrderBy.DESCENDING) for direction in order_by.values()):
            raise ValueError('order_by directions must be ASC or DESC')
        self._invalidate()
        self.order_by_fields = order_by
        return self

    async def create(
        self,
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
        self.run_select_related = False
        primary_key_field = self.ModelMeta.primary_key

        model_obj = self._model_instance(kwargs)
        PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)

        model_dict = model_obj.model_dump(include=set(self.model_fields), context={'db_write': True})
        PreCreateProcessors.model_dict_populate_auto_generated_fields(model_dict, self.Model)

        col_names = model_dict.keys()
        columns = ', '.join(col_names)
        placeholders = ', '.join(f':{col}' for col in col_names)

        # Base query
        query = f'INSERT INTO {self.table} ({columns}) VALUES ({placeholders})'

        query += f" RETURNING {primary_key_field} AS new_id"

        try:
            new_id = await self.write_connection.execute(
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
        on_conflict:str,
        conflict_target:list[str]|None=None,  # Required for "update"
        update_fields:list[str]|None=None,     # Required for "update"
        skip_validations:bool=False,
    ):
        """
        Usage
        await db.bulk_create(values=payload, on_conflict=OnConflict.DO_NOTHING)
        await db.bulk_create(
            values=payload,
            on_conflict=OnConflict.UPDATE,
            conflict_target=["id"],  # or other unique constraint columns
            update_fields=["name", "email"]
        )
        """
        if len(values) == 0:
            raise NothingToCreateError()

        self._validate_columns(conflict_target or [])
        self._validate_columns(update_fields or [])

        self.run_select_related = False
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
            model_dict = model_obj.model_dump(include=set(self.model_fields), context={'db_write': True})
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
                raise TypeError("conflict_target and update_fields must be provided for OnConflict.UPDATE")
            target = ', '.join(conflict_target)
            updates = ', '.join(f"{field} = EXCLUDED.{field}" for field in update_fields)
            query += f" ON CONFLICT ({target}) DO UPDATE SET {updates}"

        try:
            await self.write_connection.execute_many(
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
        self.run_select_related = False
        created = False
        try:
            obj = await self.get(**kwargs)
        except DoesNotExist:
            data = {**kwargs, **defaults}
            obj = await self.create(**data)
            created = True
        return obj, created

    async def update_or_create(self, defaults:dict[str, Any], **kwargs):
        self.run_select_related = False
        created = False
        try:
            obj = await self.get(**kwargs)
            data = {**obj.model_dump(), **defaults}
            obj = self._model_instance(data)
            await obj.save()
        except MultipleRecordsFound as e:
            raise e
        except DoesNotExist:
            data = {**kwargs, **defaults}
            obj = await self.create(**data)
            created = True
        return obj, created

    def update(self, **kwargs) -> Self:
        """Update records matching the query with provided values."""
        if not (self.where_conditions or self.related_where_conditions):
            raise UnrestrictedUpdateError()
        if not kwargs:
            raise ValueError('update requires at least one field')
        self._invalidate()
        self.action = QueryAction.UPDATE
        assignments = {}
        field_params = {}
        self.update_param_values = {}
        for index, (key, value) in enumerate(kwargs.items()):
            field, _, op = key.partition('__')
            self._validate_columns([field])
            if op in ('', 'jsonb'):
                field_params[field] = {}
            params = field_params.setdefault(field, {})
            param = f'set_{field}_{index}'
            expression = assignments.get(field, field)
            if op in RENDER_UPDATE_SUFFIXES:
                expression = RENDER_UPDATE_SUFFIXES[op](f'({expression})', f':{param}')
            elif op == 'jsonb':
                expression = f':{param}'
                value = json.dumps(value, cls=CustomJsonEncoder)
            elif op.startswith('jsonb_set__'):
                path = f'path_{field}_{index}'
                params[path] = [op[len('jsonb_set__'):]]
                expression = f'jsonb_set({expression}, CAST(:{path} AS text[]), :{param}, true)'
                value = json.dumps(value, cls=CustomJsonEncoder)
            elif op:
                raise UnsupportedOperatorError(message=f'Invalid operation "{op}" in update. Options are jsonb, jsonb_set, {", ".join(RENDER_UPDATE_SUFFIXES.keys())}')
            else:
                expression = f':{param}'
            assignments[field] = expression
            params[param] = value

        self.update_clause = ', '.join(f'{field}={expression}' for field, expression in assignments.items())
        self.update_param_values = {key: value for params in field_params.values() for key, value in params.items()}

        return self

    async def _update(self) -> int:
        if not self.query_executed:
            where, values = self._query_conditions()
            self.query = f'''
                WITH updated AS (
                    UPDATE {self.table} t
                    SET {self.update_clause}
                    WHERE {where}
                    RETURNING {self.ModelMeta.primary_key} AS updated_id
                ) SELECT COUNT(*) AS updated_count FROM updated;'''
            
            try:
                self.records = await self.write_connection.execute(
                    query=self.query, values={**values, **self.update_param_values})
                self.query_executed = True
            except Exception as e:
                try:
                    sqlstate = e.sqlstate
                except AttributeError:
                    raise e
                raise DatabaseError(
                    name=type(e).__name__,
                    sqlstate=sqlstate,
                    message=str(e))

        return self.records

    def delete(self) -> Self:
        """Delete records matching the query."""
        if not (self.where_conditions or self.related_where_conditions):
            raise UnrestrictedDeleteError()
        self._invalidate()
        self.action = QueryAction.DELETE
        return self

    async def _delete(self) -> int:
        if not self.query_executed:
            where, values = self._query_conditions()
            self.query = f'''
                WITH deleted AS (
                    DELETE FROM {self.table} t
                    WHERE {where}
                    RETURNING {self.ModelMeta.primary_key} AS deleted_id
                ) SELECT COUNT(*) AS deleted_count FROM deleted;'''

            try:
                self.records = await self.write_connection.execute(
                    query=self.query, values=values)
                self.query_executed = True
            except Exception as e:
                try:
                    sqlstate = e.sqlstate
                except AttributeError:
                    raise e
                raise DatabaseError(
                    name=type(e).__name__,
                    sqlstate=sqlstate,
                    message=str(e))

        return self.records

    def return_as(self, return_type:str) -> Self:
        self._invalidate()
        self.return_type = return_type
        return self

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        if self.run_lock_for_update:
            if self.action != QueryAction.FILTER or not (self.where_conditions or self.related_where_conditions):
                raise MalformedQuerysetError(self.Model.__name__, 'lock_for_update requires filter() conditions')
            if self.order_by_fields or self.fetch_limit is not None or self.fetch_offset is not None:
                raise MalformedQuerysetError(self.Model.__name__, 'lock_for_update cannot use order_by(), limit() or offset()')
        if self.action == QueryAction.UPDATE:
            return await self._update()
        elif self.action == QueryAction.DELETE:
            return await self._delete()
        elif self.action == QueryAction.GET:
            func = self._get
        elif self.action == QueryAction.FILTER:
            func = self._filter
        elif self.action == QueryAction.ALL:
            func = self._all
        elif self.action == QueryAction.COUNT:
            func = self._count
        else:
            raise MalformedQuerysetError(self.Model.__name__)

        if not self.query_executed:
            if self.action == QueryAction.COUNT:
                result = await self._execute_query(func)
            elif self.run_prefetch_related:
                result = await self._execute_query_with_prefetch_related(func)
            elif self.run_select_related:
                result = await self._execute_query_with_select_related(func)
            else:
                result = await self._execute_query(func)
            self.query_executed = True
            return result
        return func()


class AsyncRawQuery:

    def __init__(self, query:str, using:str|None=None):
        self.query = query
        self.values = None
        fastpg = get_fastpg()
        if using:
            self.read_connection = fastpg.db_conn_manager.get_db_conn(using)
        else:
            self.read_connection = fastpg.db_conn_manager.db_for_read()
        self.write_connection = fastpg.db_conn_manager.db_for_write()
    
    def render_in_clauses(self, values:Dict[str, Any]) -> Dict[str, Any]:
        _values = {**values}
        for param_name, param_val in values.items():
            if isinstance(param_val, InClauseParam):
                in_clause_param_names, in_clause_param_values = param_val.render(param_name)
                self.query = self.query.replace(f':{param_name}', in_clause_param_names)
                del _values[param_name]
                _values = {**_values, **in_clause_param_values}
        return _values

    async def fetch(self, values:Dict[str, Any]) -> List[Dict[str, Any]]:
        self.values = self.render_in_clauses(values)
        try:
            records = await self.read_connection.fetch_all(
                query=self.query, values=self.values)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
        return [dict(record) for record in records]
    
    async def execute(self, values:Dict[str, Any]) -> List[Record]:
        self.values = self.render_in_clauses(values)
        try:
            return await self.write_connection.execute(
                query=self.query, values=self.values)
        except TypeError as e:
            raise e
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            if sqlstate == '23505':
                raise DuplicateKeyDatabaseError(
                    table_name=None,
                    sqlstate=sqlstate,
                    message=str(e))
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
    
    async def execute_many(self, list_of_values: List[Dict[str, Any]]) -> List[Record]:
        self.values = []
        for v in list_of_values:
            self.values.append(self.render_in_clauses(v))
        try:
            return await self.write_connection.execute_many(
                query=self.query, list_of_values=self.values)
        except TypeError as e:
            raise e
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            if sqlstate == '23505':
                raise DuplicateKeyDatabaseError(
                    table_name=None,
                    sqlstate=sqlstate,
                    message=str(e))
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))


class queryset_property:
    """Descriptor that works like @property but for classes."""
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner_cls):
        return self.func(owner_cls)
        

class DatabaseModel(BaseModel):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        parts = cls.__module__.split(".")
        app_label = parts[-2] if parts[-1] == "models" else parts[-1]
        _FASTPG_MODELS[f'{app_label}.{cls.__name__}'] = cls

    async_queryset:ClassVar[AsyncQuerySet]
    _write_connection:Optional[AsyncPostgresDBConnection] = PrivateAttr(default=None)

    model_config = ConfigDict(extra='allow')
    
    @queryset_property
    def async_queryset(cls):
        return AsyncQuerySet(model=cls)

    @property
    def write_connection(self):
        if self._write_connection is None:
            self._write_connection = get_fastpg().db_conn_manager.db_for_write()
        return self._write_connection

    async def pre_save(self) -> None:
        pass

    async def post_save(self) -> None:
        pass

    async def save(self, columns:Optional[List[str]]=None) -> bool:
        await self.pre_save()

        PreSaveProcessors.model_obj_populate_auto_now_fields(self)

        values = {}
        model_dict = self.model_dump(include=set(type(self).model_fields), context={'db_write': True})

        if columns is None:
            columns = model_dict.keys()

        for col in columns:
            values[col] = model_dict[col]

        set_clause = ', '.join(f'{col}=:{col}' for col in columns)
        where_clause = f'{self.Meta.primary_key} = :{self.Meta.primary_key}'
        values[self.Meta.primary_key] = model_dict[self.Meta.primary_key]

        query = f'''
            WITH updated AS (
                UPDATE {self.Meta.db_table} t
                SET {set_clause}
                WHERE {where_clause}
                RETURNING {self.Meta.primary_key} AS updated_id
            ) SELECT COUNT(*) AS updated_count FROM updated;'''

        try:
            updated_count = await self.write_connection.execute(
                query=query, values=values)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))

        if updated_count:
            await self.post_save()

        return bool(updated_count)

    async def delete(self) -> bool:
        model_dict = self.model_dump(context={'db_write': True})
        values = {}
        for key in model_dict.keys():
            if key == self.Meta.primary_key:
                values[key] = model_dict[key]
                break

        where_clause = f'{self.Meta.primary_key} = :{self.Meta.primary_key}'
        query = f'''
            WITH deleted AS (
                DELETE FROM {self.Meta.db_table} t
                WHERE {where_clause}
                RETURNING {self.Meta.primary_key} AS deleted_id
            ) SELECT COUNT(*) AS deleted_count FROM deleted;'''

        try:
            deleted_count = await self.write_connection.execute(
                query=query, values=values)
        except Exception as e:
            try:
                sqlstate = e.sqlstate
            except AttributeError:
                raise e
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
        
        return bool(deleted_count)


class Transaction:

    @staticmethod
    def atomic():
        fastpg = get_fastpg()
        return fastpg.db_conn_manager.transaction()
    
    @staticmethod
    async def start():
        fastpg = get_fastpg()
        return await fastpg.db_conn_manager.transaction()
    
    @staticmethod
    def decorator():
        def _decorator(fn):
            async def _wrapped(*args, **kwargs):
                async with Transaction.atomic():
                    return await fn(*args, **kwargs)
            return _wrapped
        return _decorator
