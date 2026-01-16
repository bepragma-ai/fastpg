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
    'jsonb_remove': lambda field, value: f"{field}={field} - '{value}'",
    'add': lambda field, value: f'{field}={field} + {value}',
    'sub': lambda field, value: f'{field}={field} - {value}',
    'mul': lambda field, value: f'{field}={field} * {value}',
    'div': lambda field, value: f'{field}={field} / {value}',
    'add_time': lambda field, value: f"{field}={field} + interval '{value}'",
    'sub_time': lambda field, value: f"{field}={field} - interval '{value}'",
}


class OrderBy:
    DESCENDING = 'DESC'
    ASCENDING = 'ASC'


class OnConflict:
    DO_NOTHING = 'DO_NOTHING'
    UPDATE = 'UPDATE'


class ReturnType:
    MODEL_INSTANCE = 'MODEL_INSTANCE'
    DICT = 'DICT'
