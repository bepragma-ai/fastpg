from .constants import OrderBy
from .constants import OnConflict
from .constants import ReturnTypes

from .utils import Relation
from .utils import Q

from .core import DatabaseModel
from .core import AsyncRawQuery

from .paginator import AsyncPaginator
from .paginator import RawQueryAsyncPaginator

from .errors import DatabaseError
from .errors import DuplicateKeyDatabaseError
from .errors import DoesNotExist
from .errors import MulipleRecordsFound
from .errors import UnsupportedOperatorError


def get_package_info() -> dict:
    """
    Get package information
    
    Returns:
        dict: Package information
    """
    return {
        "name": "fastpg",
        "version": "0.1.0",
        "description": "A light wieght ORM for FastAPI projects and Postgresql"
    }


__all__ = [
    "OrderBy",
    "OnConflict",
    "ReturnTypes",
    "Relation",
    "Q",
    "DatabaseModel",
    "AsyncRawQuery",
    "AsyncPaginator",
    "RawQueryAsyncPaginator",
    "DatabaseError",
    "DuplicateKeyDatabaseError",
    "DoesNotExist",
    "MulipleRecordsFound",
    "UnsupportedOperatorError",
    "get_package_info",
]
