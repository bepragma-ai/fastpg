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


class OrderBy:
    DESCENDING = 'DESC'
    ASCENDING = 'ASC'


class OnConflict:
    DO_NOTHING = 'DO_NOTHING'
    UPDATE = 'UPDATE'


class ReturnTypes:
    MODEL_INSTANCE = 'MODEL_INSTANCE'
    DICT = 'DICT'
