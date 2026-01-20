from typing import List


class ReadConnectionNotAvailableError(Exception):

    def __init__(self) -> None:
        self.message = 'At least one read connection must be provided. Check your databases configuration.'
        super().__init__(self.message)


class MultipleWriteConnectionsError(Exception):

    def __init__(self) -> None:
        self.message = 'Multiple write connections are not allowed. Check your databases configuration.'
        super().__init__(self.message)


class InvalidConnectionNameError(Exception):

    def __init__(self, conn_name:str) -> None:
        self.conn_name = conn_name
        self.message = f'Invalid connection name "{conn_name}"'
        super().__init__(self.message)


class FastPGInstanceNotConfiguredError(Exception):

    def __init__(self, instance_name:str) -> None:
        self.instance_name = instance_name
        self.message = f'FastPG instance "{instance_name}" is not configured'
        super().__init__(self.message)


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


class DuplicateKeyDatabaseError(DatabaseError):

    def __init__(self, table_name:str, sqlstate:int, message:str) -> None:
        self.table_name = table_name
        self.sqlstate = sqlstate
        self.message = f'(SQLSTATE {sqlstate}): {message} of table "{table_name}"'
        super().__init__(self.table_name, self.sqlstate, self.message)


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


class MultipleRecordsFound(Exception):
    """Raised when a query expecting a single record returns multiple results."""

    def __init__(self, model_name: str, query: str) -> None:
        self.message = f"Multiple {model_name} objects for query: {query}"
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


class InvalidRelatedFieldError(Exception):

    def __init__(self, model_name:str, relation_name:str, valid_relation_names:List[str]) -> None:
        valid_relation_names = ','.join(f'"{name}"' for name in valid_relation_names)
        self.message = f'Model "{model_name}" does not have any related field named "{relation_name}". Options are: {valid_relation_names}'
        super().__init__(self.message)


class InvalidPrefetchError(Exception):

    def __init__(self, model_name:str, prefetch_model_name:str) -> None:
        self.message = f'Model "{model_name}" does not have any relation defined with "{prefetch_model_name}"'
        super().__init__(self.message)
