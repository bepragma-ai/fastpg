import os
import time
import random
import functools

from .constants import OPERATORS
from .errors import (
    InvalidINClauseValueError,
    UnsupportedOperatorError,
    MalformedMetaError,
)


import logging
logger = logging.getLogger(__name__)

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'UNNAMED').upper()
LOG_DB_QUERIES = os.environ.get('LOG_DB_QUERIES', 'false').upper() == 'TRUE'


class Relation:

    def __init__(self, related_model, base_field:str, foreign_field:str, related_data_set_name:str=None) -> None:
        self.RelatedModel = related_model
        try:
            self.table = self.RelatedModel.Meta.db_table
        except AttributeError as e:
            if str(e) == 'Meta':
                raise MalformedMetaError(self.RelatedModel.__name__)
        self.model_fields = self.RelatedModel.__fields__.keys()
        self.base_field = base_field
        self.foreign_field = foreign_field
        self.related_data_set_name = related_data_set_name if related_data_set_name else f'{self.RelatedModel.__name__.lower()}_set'
    
    def set_related_data_set_name(self, related_data_set_name:str) -> None:
        self.related_data_set_name = related_data_set_name
    
    def render_on_clause(self) -> str:
        return f't.{self.base_field} = r.{self.foreign_field}'


class Q:

    def __init__(self, query=None, params=None, **kwargs):
        self.secret = random.randint(0, 9999)
        if query:
            self.where_clause = query
            self.params = params or {}
        else:
            conditions, self.params = [], {}
            for key, value in kwargs.items():
                if '__' in key:
                    field, op = key.split('__', 1)
                    field_name = f'{field}_{self.secret}'

                    try:
                        operator = OPERATORS[op]
                    except KeyError:
                        raise UnsupportedOperatorError(f'Unsupported operator: {op}. Options are: {", ".join(OPERATORS.keys())}')
                    
                    if operator == 'IN':
                        if not isinstance(value, list):
                            raise InvalidINClauseValueError(
                                f'IN clause value for "{field}" must be supplied with a "list" type and not "{type(value).__name__}" type')

                        sub_fields = []
                        for idx, sub_val in enumerate(value):
                            sub_fields.append(f':{field_name}_{idx}')
                            self.params[f'{field_name}_{idx}'] = sub_val
                        
                        conditions.append(f"{field} IN ({','.join(sub_fields)})")

                    elif operator == 'IS NULL':
                        if value:
                            conditions.append(f'{field} IS NULL')
                        else:
                            conditions.append(f'{field} IS NOT NULL')

                    elif operator in ('ILIKE', 'LIKE'):
                        if op in ('contains', 'icontains'):
                            value = f'%{value}%'
                        elif op in ('startswith', 'istartswith'):
                            value = f'{value}%'
                        elif op in ('endswith', 'iendswith'):
                            value = f'%{value}'
                        conditions.append(f'{field} {operator} :{field_name}')
                        self.params[f'{field_name}'] = value

                    else:
                        conditions.append(f'{field} {operator} :{field_name}')
                        self.params[f'{field_name}'] = value

                else:
                    field_name = f'{key}_{self.secret}'
                    conditions.append(f'{key} = :{field_name}')
                    self.params[f'{field_name}'] = value
            
            self.where_clause = ' AND '.join(conditions)

    def __or__(self, other):
        combined_query = f"({self.where_clause} OR {other.where_clause})"
        combined_params = {**self.params, **other.params}
        return Q(query=combined_query, params=combined_params)
    
    def __and__(self, other):
        combined_query = f"({self.where_clause} AND {other.where_clause})"
        combined_params = {**self.params, **other.params}
        return Q(query=combined_query, params=combined_params)

    def __repr__(self):
        return f"{self.where_clause} {self.params}"


def async_sql_logger(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if LOG_DB_QUERIES:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            if elapsed_time < 1.0:
                logger.info(f"{PROJECT_NAME}_QUERY_LT_1_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 5.0:
                logger.info(f"{PROJECT_NAME}_QUERY_1_5_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 10.0:
                logger.info(f"{PROJECT_NAME}_QUERY_5_10_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            else:
                logger.info(f"{PROJECT_NAME}_QUERY_GT_10_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")

            return result
        
        return await func(*args, **kwargs)

    return wrapper


def sync_sql_logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if LOG_DB_QUERIES:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            if elapsed_time < 1.0:
                logger.info(f"{PROJECT_NAME}_QUERY_LT_1_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 5.0:
                logger.info(f"{PROJECT_NAME}_QUERY_1_5_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            elif elapsed_time < 10.0:
                logger.info(f"{PROJECT_NAME}_QUERY_5_10_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")
            else:
                logger.info(f"{PROJECT_NAME}_QUERY_GT_10_SEC [took {elapsed_time:.4f}s]: {kwargs['query']}")

            return result
        
        return func(*args, **kwargs)

    return wrapper
