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


from .constants import ConnectionType
from .constants import OrderBy
from .constants import OnConflict
from .constants import ReturnType

from .utils import Prefetch
from .utils import Relation
from .utils import Q

from .fields import (
    JsonData,
    json_str_to_dict,
    serialize_json_data,
    validate_json_data,
)

from .paginator import AsyncPaginator
from .paginator import RawQueryAsyncPaginator

from .errors import (
    InvalidConnectionNameError,
    DatabaseError,
    DuplicateKeyDatabaseError,
    DoesNotExist,
    MultipleRecordsFound,
    UnsupportedOperatorError,
    MultipleRecordsFound,
)

from .core import DatabaseModel
from .core import AsyncQuerySet
from .core import AsyncRawQuery
from .core import queryset_property
from .core import Transaction

from .fastpg import (
    create_fastpg,
    register_fastpg,
    get_fastpg,
    set_current_fastpg,
    DBConnectionManager,
)


__all__ = [
    "create_fastpg",
    "register_fastpg",
    "get_fastpg",
    "set_current_fastpg",
    "DBConnectionManager",
    "ConnectionType",
    "OrderBy",
    "OnConflict",
    "ReturnType",
    "Prefetch",
    "Relation",
    "Q",
    "DatabaseModel",
    "AsyncQuerySet",
    "AsyncRawQuery",
    "queryset_property",
    "Transaction",
    "JsonData",
    "json_str_to_dict",
    "serialize_json_data",
    "validate_json_data",
    "AsyncPaginator",
    "RawQueryAsyncPaginator",
    "InvalidConnectionNameError",
    "DatabaseError",
    "DuplicateKeyDatabaseError",
    "DoesNotExist",
    "MultipleRecordsFound",
    "MultipleRecordsFound",
    "UnsupportedOperatorError",
]
