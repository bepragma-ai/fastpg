from functools import reduce
from typing import Any, ClassVar, Dict, List
from typing_extensions import Self
import json

from pydantic import BaseModel, ConfigDict

from databases.backends.common.records import Record

from .constants import (
    ReturnType,
    OnConflict,
    RENDER_UPDATE_SUFFIXES,
)

from .utils import (
    Relation,
    Prefetch,
    Q,
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
)

from .preprocessors import (
    PreCreateProcessors,
    PreSaveProcessors,
)

from .fastpg import FAST_PG


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

        self.action = None
        self.base_query = None
        self.query = None
        self.query_executed = False

        self.conditions = []
        self.where_conditions = ''
        self.query_param_values = {}
        self.related_conditions = []
        self.related_where_conditions = ''
        self.related_query_param_values = {}

        self.fetch_limit = None
        self.fetch_offset = None
        self.order_by_fields = None

        self.records = None

        self.run_select_related = False
        self.relation:Relation = None
        
        self.run_prefetch_related = False
        self.prefetches:List[Prefetch] = []

        self.update_clause = None

        self.return_type = ReturnType.MODEL_INSTANCE

        self.read_connection = FAST_PG.db_for_read()
        self.write_connection = FAST_PG.db_for_write()

    def _reduce_conditions(self, *args, **kwargs) -> Q:
        if kwargs:
            self.conditions.append(Q(**kwargs))
        if args:
            self.conditions.extend(args)
        return reduce(lambda x, y: x & y, self.conditions)
    
    def _reduce_related_conditions(self, *args, **kwargs) -> Q:
        if kwargs:
            self.related_conditions.append(Q(relation=self.relation, **kwargs))
        if args:
            self.related_conditions.extend(args)
        return reduce(lambda x, y: x & y, self.related_conditions)

    def _denormalize_related_data(self) -> list[dict]:
        items = []
        for record in self.records:
            related_id_field_val = record[f'r_{self.relation.related_id_field}']

            item = {f: record[f't_{f}'] for f in self.columns_to_fetch}
            item[self.relation.related_name] = None
            if related_id_field_val:
                item[self.relation.related_name] = {f: record[f'r_{f}'] for f in self.relation.model_fields}
            
            items.append(item)
        return items

    def _serialize_data(self) -> None:
        if self.action == 'count':
            return

        if self.return_type == ReturnType.MODEL_INSTANCE:
            if self.run_select_related:
                model_objs = []
                for record in self.records:
                    related_record = record[self.relation.related_name]
                    related_obj = self.relation.RelatedModel(**related_record) if related_record else None
                    model_obj = self.Model(**record)
                    setattr(model_obj, self.relation.related_name, related_obj)
                    model_objs.append(model_obj)
                self.records = model_objs
            else:
                self.records = [self.Model(**record) for record in self.records]
        else:
            # Return as list of dict
            self.records = [{**record} for record in self.records]

    async def _execute_query(self, func) -> None:
        self.query = f'{self.base_query} WHERE {self.where_conditions}' if self.where_conditions else self.base_query

        if self.order_by_fields:
            self.query += ' ORDER BY ' + ','.join(f'{k} {v}' for k, v in self.order_by_fields.items())
        if self.fetch_limit:
            self.query += f' LIMIT {self.fetch_limit}'
        if self.fetch_offset:
            self.query += f' OFFSET {self.fetch_offset}'
        
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
        return func()

    async def _execute_query_with_select_related(self, func) -> None:
        main_table_fields = ','.join(f't.{f} AS t_{f}' for f in self.columns_to_fetch)
        related_table_fields = ','.join(f'r.{f} AS r_{f}' for f in self.relation.model_fields)

        self.query = f"""
            SELECT {main_table_fields}, {related_table_fields}
            FROM {self.table} t LEFT JOIN {self.relation.table} r
            ON {self.relation.render_on_clause()}
        """
        if self.where_conditions:
            self.query += f'WHERE {self.where_conditions}'
            if self.related_where_conditions:
                self.query += f' AND {self.related_where_conditions}'
        else:
            if self.related_where_conditions:
                self.query += f' WHERE {self.related_where_conditions}'
        if self.order_by_fields:
            _clauses = []
            for k, v in self.order_by_fields.items():
                _clauses.append(f't.{k} {v}')
            self.query += ' ORDER BY ' + ','.join(_clauses)
        if self.fetch_limit:
            self.query += f' LIMIT {self.fetch_limit}'
        if self.fetch_offset:
            self.query += f' OFFSET {self.fetch_offset}'

        try:
            self.records = await self.read_connection.fetch_all(
                query=self.query, values={
                    **self.query_param_values,
                    **self.related_query_param_values})
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

        self.records = self._denormalize_related_data()
        self._serialize_data()
        return func()
    
    async def _execute_query_with_prefetch_related(self, func) -> None:
        base_objs = await self._execute_query(func)
        if not isinstance(base_objs, list):
            base_objs = [base_objs]
        
        if len(base_objs) == 0:
            return func()

        if self.return_type == ReturnType.MODEL_INSTANCE:
            for prefetch in self.prefetches:
                id_field_vals = [getattr(i, prefetch.id_field) for i in base_objs]
                id_filter = {}
                id_filter[f'{prefetch.foreign_field}__in'] = id_field_vals
                prefetch_objs = await prefetch.queryset.filter(**id_filter)

                for base_obj in base_objs:
                    prefetch_obj_set = []
                    for prefetch_obj in prefetch_objs:
                        if getattr(base_obj, prefetch.id_field) == getattr(prefetch_obj, prefetch.foreign_field):
                            prefetch_obj_set.append(prefetch_obj)
                    setattr(base_obj, prefetch.dataset_name, prefetch_obj_set)
        else:
            for prefetch in self.prefetches:
                id_field_vals = [i[prefetch.id_field] for i in base_objs]
                id_filter = {}
                id_filter[f'{prefetch.foreign_field}__in'] = id_field_vals
                prefetch_objs = await prefetch.queryset.filter(**id_filter).return_as(ReturnType.DICT)

                for base_obj in base_objs:
                    prefetch_obj_set = []
                    for prefetch_obj in prefetch_objs:
                        if base_obj[prefetch.id_field] == prefetch_obj[prefetch.foreign_field]:
                            prefetch_obj_set.append(prefetch_obj)
                    base_obj[prefetch.dataset_name] = prefetch_obj_set

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
        self.read_connection = FAST_PG.get_db_conn(conn_name)
        return self

    def columns(self, *columns:set[str]) -> Self:
        self.columns_to_fetch = list(columns)
        return self

    def get(self, *args, **kwargs) -> Self:
        """Fetch a single record matching the given conditions."""
        self.action = 'get'

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
        all_conditions = self._reduce_related_conditions(*args, **kwargs)
        self.related_where_conditions = all_conditions.where_clause
        self.related_query_param_values = all_conditions.params

        return self

    def filter(self, *args, **kwargs) -> Self:
        """Filter records based on provided conditions."""
        self.action = 'filter'

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table} t'

        all_conditions = self._reduce_conditions(*args, **kwargs)
        self.where_conditions = all_conditions.where_clause
        self.query_param_values = all_conditions.params

        return self

    def _filter(self):
        return self.records

    def all(self) -> Self:
        """Select all records for the model."""
        self.action = 'all'

        columns_to_fetch = ','.join(list(self.columns_to_fetch))
        self.base_query = f'SELECT {columns_to_fetch} FROM {self.table} t'

        self.where_conditions = ''
        self.query_param_values = {}
        return self

    def _all(self):
        return self.records

    def count(self) -> Self:
        """Count the number of records matching the query."""
        self.action = 'count'
        self.run_select_related = False
        self.base_query = f'SELECT count({self.ModelMeta.primary_key}) FROM {self.table} t'
        return self

    def _count(self) -> int:
        record_count = len(self.records)
        if record_count == 1:
            return self.records[0]['count']

    def select_related(self, *relation_names:List[str]) -> Self:
        self.run_select_related = True
        relation_name = relation_names[0]
        try:
            self.relation = self.ModelMeta.relations[relation_name]
        except KeyError:
            raise InvalidRelatedFieldError(self.Model.__name__, relation_name, self.ModelMeta.relations.keys())
        return self
    
    def prefetch_related(self, *prefetches:List[Prefetch]) -> Self:
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
        self.fetch_limit = fetch_limit
        return self

    def offset(self, fetch_offset:int) -> Self:
        self.fetch_offset = fetch_offset
        return self

    def order_by(self, **order_by) -> Self:
        self.order_by_fields = order_by
        return self

    async def create(
        self,
        on_conflict:str=None,  # Options: None | "ignore" | "update"
        conflict_target:list[str]=None,  # Required for "update"
        update_fields:list[str]=None,    # Required for "update"
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

        model_obj = self.Model(**kwargs)
        PreCreateProcessors.model_obj_populate_auto_now_add_fields(model_obj)

        model_dict = model_obj.model_dump(context={'db_write': True})
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
            print('++++++++++++++++++++++++++++++++++++++++++++')
            print(self.write_connection)
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
            model_dict = model_obj.model_dump(context={'db_write': True})
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
            obj = self.Model(**data)
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
        if self.where_conditions is None:
            raise UnrestrictedUpdateError()
        
        self.action = 'update'
        self.run_select_related = False
        _update_clause = []
        for key in kwargs.keys():
            if "__" in key:
                field, op = key.split("__", 1)
                value = kwargs[key]
                try:
                    _update_clause.append(RENDER_UPDATE_SUFFIXES[op](field, value))
                except KeyError:
                    if op == 'jsonb':
                        _update_clause.append(f'{field}=:set_{field}')
                        self.query_param_values[f'set_{field}'] = json.dumps(value, cls=CustomJsonEncoder)
                    else:
                        op_pieces = op.split("__")
                        if op_pieces[0] == 'jsonb_set':
                            try:
                                op = op_pieces[0]
                                field_to_update = op_pieces[1]
                            except IndexError:
                                raise UnsupportedOperatorError(message=f'Missing jsonb key name for operation "{op}" in update')
                            _update_clause.append(f"{field}=jsonb_set({field}, '{{{field_to_update}}}', :set_{field_to_update}, true)")
                            self.query_param_values[f'set_{field_to_update}'] = json.dumps(value, cls=CustomJsonEncoder)  # Always send JSON string regardless of the data type
                        else:
                            raise UnsupportedOperatorError(message=f'Invalid operation "{op}" in update. Options are jsonb, jsonb_set, {", ".join(RENDER_UPDATE_SUFFIXES.keys())}')
            else:
                _update_clause.append(f'{key}=:set_{key}')
                self.query_param_values[f'set_{key}'] = kwargs[key]

        self.update_clause = ', '.join(_update_clause)

        return self

    async def _update(self) -> int:
        if not self.query_executed:
            self.query = f'''
                WITH updated AS (
                    UPDATE {self.table} t
                    SET {self.update_clause}
                    WHERE {self.where_conditions}
                    RETURNING {self.ModelMeta.primary_key} AS updated_id
                ) SELECT COUNT(*) AS updated_count FROM updated;'''
            
            try:
                self.records = await self.write_connection.execute(
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

        return self.records

    def delete(self) -> Self:
        """Delete records matching the query."""
        if self.where_conditions is None:
            raise UnrestrictedDeleteError()

        self.action = 'delete'
        self.run_select_related = False
        return self

    async def _delete(self) -> int:
        if not self.query_executed:
            self.query = f'''
                WITH deleted AS (
                    DELETE FROM {self.table} t
                    WHERE {self.where_conditions}
                    RETURNING {self.ModelMeta.primary_key} AS deleted_id
                ) SELECT COUNT(*) AS deleted_count FROM deleted;'''

            try:
                self.records = await self.write_connection.execute(
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
            if self.run_select_related:
                return self._execute_query_with_select_related(func).__await__()
            elif self.run_prefetch_related:
                return self._execute_query_with_prefetch_related(func).__await__()
            else:
                return self._execute_query(func).__await__()


class AsyncRawQuery:

    def __init__(self, query:str, connection:AsyncPostgresDBConnection=None):
        self.query = query
        self.read_connection = connection or FAST_PG.db_for_read()
        self.write_connection = FAST_PG.db_for_write()

    async def fetch(self, values:dict[str, Any]) -> List[Record]:
        self.values = values
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
    
    async def execute(self, values:dict[str, Any]) -> List[Record]:
        self.values = values
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
                    table_name=self.table,
                    sqlstate=sqlstate,
                    message=str(e))
            raise DatabaseError(
                name=type(e).__name__,
                sqlstate=sqlstate,
                message=str(e))
    
    async def execute_many(self, list_of_values: List[Dict]) -> list[Record]:
        self.values = list_of_values
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
                    table_name=self.table,
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
    async_queryset:ClassVar[AsyncQuerySet]
    write_connection:ClassVar[AsyncPostgresDBConnection]

    model_config = ConfigDict(extra='allow')
    
    @queryset_property
    def async_queryset(cls):
        cls.write_connection = FAST_PG.db_for_write()
        return AsyncQuerySet(model=cls)
    
    async def save(self, columns:List[str]=None) -> bool:
        PreSaveProcessors.model_obj_populate_auto_now_fields(self)

        values = {}
        model_dict = self.model_dump(context={'db_write': True})

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
