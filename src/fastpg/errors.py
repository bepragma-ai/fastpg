class MalformedMetaError(Exception):

    def __init__(self, model_name:str) -> None:
        self.message = f'Meta class is either missing or malformed for DBModel "{model_name}"'
        super().__init__(self.message)


class MalformedQuerysetError(Exception):

    def __init__(self, model_name:str) -> None:
        self.message = f'"{model_name}" queryset is invalid: one among get, filter, all, count must be called'
        super().__init__(self.message)


class DatabaseError(Exception):

    def __init__(self, name:str, sqlstate:int, message:str='A database error has occurred') -> None:
        self.name = name
        self.sqlstate = sqlstate
        self.message = f'(SQLSTATE {sqlstate}): {message}'
        super().__init__(self.message)


class DuplicateKeyDatabaseError(Exception):

    def __init__(self, table_name:str, sqlstate:int, message:str) -> None:
        self.table_name = table_name
        self.sqlstate = sqlstate
        self.message = f'(SQLSTATE {sqlstate}): {message} of table "{table_name}"'
        super().__init__(self.message)


class InvalidINClauseValueError(Exception):
    
    def __init__(self, message='IN clause must be supplied with a list') -> None:
        self.message = message
        super().__init__(self.message)


class UnsupportedOperatorError(Exception):
    
    def __init__(self, message='Invalid where clause operator found') -> None:
        self.message = message
        super().__init__(self.message)


class DoesNotExist(Exception):
    
    def __init__(self, model_name:str, query:str) -> None:
        self.message = f'{model_name} object does not exist for query: {query}'
        super().__init__(self.message)


class MulipleRecordsFound(Exception):
    
    def __init__(self, model_name:str, query:str) -> None:
        self.message = f'Multiple {model_name} objects for query: {query}'
        super().__init__(self.message)


class NothingToCreateError(Exception):

    def __init__(self, message=f'No values were supplied for bulk creation') -> None:
        self.message = message
        super().__init__(self.message)


class UnrestrictedUpdateError(Exception):

    def __init__(self, message=f'Where clause conditions must be provided to update items in database') -> None:
        self.message = message
        super().__init__(self.message)


class UnrestrictedDeleteError(Exception):

    def __init__(self, message=f'Where clause conditions must be provided to delete items from database') -> None:
        self.message = message
        super().__init__(self.message)


class InvalidPageError(Exception):

    def __init__(self, page:int) -> None:
        self.message = f'Invalid page "{page}" and must be a non-zero positive integer'
        super().__init__(self.message)
