from enum import Enum


class ConnectionType(Enum):
    READ = 'READ'
    WRITE = 'WRITE'


OPERATORS = {
    'gt': '>',
    'lt': '<',
    'gte': '>=',
    'lte': '<=',
    'ne': '!=',
    'in': 'IN',
    'isnull': 'IS NULL',
    'contains': 'LIKE',
    'icontains': 'ILIKE',
    'startswith': 'LIKE',
    'istartswith': 'ILIKE',
    'endswith': 'LIKE',
    'iendswith': 'ILIKE',
}


RENDER_UPDATE_SUFFIXES = {
    'jsonb_remove': lambda field, param: f'{field} - CAST({param} AS text)',
    'add': lambda field, param: f'{field} + {param}',
    'sub': lambda field, param: f'{field} - {param}',
    'mul': lambda field, param: f'{field} * {param}',
    'div': lambda field, param: f'{field} / {param}',
    'add_time': lambda field, param: f'{field} + CAST(CAST({param} AS text) AS interval)',
    'sub_time': lambda field, param: f'{field} - CAST(CAST({param} AS text) AS interval)',
}


class QueryAction(Enum):
    NONE = 'NONE'
    GET = 'GET'
    FILTER = 'FILTER'
    ALL = 'ALL'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    COUNT = 'COUNT'


class OrderBy:
    DESCENDING = 'DESC'
    ASCENDING = 'ASC'


class OnConflict:
    DO_NOTHING = 'DO_NOTHING'
    UPDATE = 'UPDATE'


class ReturnType:
    MODEL_INSTANCE = 'MODEL_INSTANCE'
    DICT = 'DICT'
