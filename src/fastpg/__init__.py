"""
FastPG - Lightweight async ORM for PostgreSQL and FastAPI
"""

try:
    from ._version import __version__
except ImportError:
    # Fallback for development
    __version__ = "0.0.0.dev0"

__author__ = "Eshan Das"
__email__ = "eshan@logisy.tech"


from .constants import OrderBy
from .constants import OnConflict
from .constants import ReturnTypes

from .utils import Relation
from .utils import Q

from .core import DatabaseModel
from .core import AsyncRawQuery

from .paginator import AsyncPaginator
from .paginator import RawQueryAsyncPaginator

from .errors import (
    DatabaseError,
    DuplicateKeyDatabaseError,
    DoesNotExist,
    MultipleRecordsFound,
    UnsupportedOperatorError,
    MulipleRecordsFound,
)


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
    "MultipleRecordsFound",
    "MulipleRecordsFound",
    "UnsupportedOperatorError",
]
