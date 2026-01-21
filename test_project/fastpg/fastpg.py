from contextvars import ContextVar
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
import random
import pytz

from .constants import (
    ConnectionType,
)

from .db import AsyncPostgresDBConnection

from .errors import (
    ReadConnectionNotAvailableError,
    MultipleWriteConnectionsError,
    InvalidConnectionNameError,
    FastPGInstanceNotConfiguredError,
)

from .print import print_green


class DBConnectionManager:

    def __init__(
            self,
            databases_config:Dict[str, Dict[str, str]]=None,
        ):
        self.databases_config = databases_config or {}
        self.databases = {}
        self.connections = {}
        self.read_conn_names = []
        self.write_conn_name = None
        self.transaction = None

        self.__create_connections()

    def __set_write_connection(self, conn_name:str) -> None:
        if self.write_conn_name is None:
            self.write_conn_name = conn_name
        else:
            raise MultipleWriteConnectionsError
    
    def __create_connections(self) -> None:
        for conn_name in self.databases_config:
            config = self.databases_config[conn_name]

            conn_type = config['TYPE']
            user = quote_plus(str(config['USER']))
            password = quote_plus(str(config['PASSWORD']))
            db = config['DB']
            host = config['HOST']
            port = config['PORT']

            self.connections[conn_name] = AsyncPostgresDBConnection(
                conn_name=conn_name,
                conn_type=conn_type,
                db_uri=f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}")
            
            if conn_type == ConnectionType.READ:
                self.read_conn_names.append(conn_name)
            else:
                self.__set_write_connection(conn_name)
            
        if len(self.read_conn_names) == 0:
            raise ReadConnectionNotAvailableError
    
    async def connect_all(self) -> None:
        for conn_name in self.connections:
            await self.connections[conn_name].connect()
            print_green(f'"{conn_name}" successfully connected...')
        self.transaction = self.connections[self.write_conn_name].transaction

    async def close_all(self) -> None:
        for conn_name in self.connections:
            await self.connections[conn_name].close()
            print_green(f'"{conn_name}" successfully closed...')
    
    def get_db_conn(self, conn_name:str) -> AsyncPostgresDBConnection:
        try:
            return self.connections[conn_name]
        except KeyError:
            raise InvalidConnectionNameError(conn_name)

    def db_for_read(self) -> AsyncPostgresDBConnection:
        conn_name = random.choice(self.read_conn_names)
        try:
            return self.connections[conn_name]
        except KeyError:
            raise InvalidConnectionNameError(conn_name)

    def db_for_write(self) -> AsyncPostgresDBConnection:
        try:
            return self.connections[self.write_conn_name]
        except KeyError:
            raise InvalidConnectionNameError(self.write_conn_name)


class FastPG:

    def __init__(
            self,
            databases:Dict[str, Dict[str, str]]=None,
            tz_name:str='UTC',
            query_logger:Dict[str, Any]=None,
            db_conn_manager_class:DBConnectionManager=None,
        ):
        self.tz_name = tz_name
        self.TZ = None
        self.log_title = ''
        self.log_db_queries = False
        self.db_conn_manager:DBConnectionManager = None

        if query_logger:
            self.log_title = query_logger['TITLE']
            self.log_db_queries = query_logger['LOG_QUERIES']
        self.__get_timezone()

        if db_conn_manager_class:
            self.db_conn_manager = db_conn_manager_class(databases or {})
        else:
            self.db_conn_manager = DBConnectionManager(databases or {})

    def __get_timezone(self) -> None:
        try:
            self.TZ = pytz.timezone(self.tz_name)
        except pytz.UnknownTimeZoneError:
            self.TZ = pytz.UTC


_FASTPG_REGISTRY: Dict[str, "FastPG"] = {}
_CURRENT_FASTPG_NAME:ContextVar[str] = ContextVar("fastpg_current_name", default="default")


def register_fastpg(name:str, instance:"FastPG") -> None:
    _FASTPG_REGISTRY[name] = instance


def create_fastpg(
        name:str="default",
        databases:Dict[str, Dict[str, str]]=None,
        tz_name:str='UTC',
        query_logger:Dict[str, Any]=None,
        db_conn_manager_class:DBConnectionManager=None,
    ) -> "FastPG":
    instance = FastPG(
        databases=databases,
        tz_name=tz_name,
        query_logger=query_logger,
        db_conn_manager_class=db_conn_manager_class)

    register_fastpg(name, instance)
    _CURRENT_FASTPG_NAME.set(name)

    return instance


def get_fastpg(name:Optional[str]=None) -> "FastPG":
    resolved_name = name or _CURRENT_FASTPG_NAME.get()
    try:
        return _FASTPG_REGISTRY[resolved_name]
    except KeyError:
        raise FastPGInstanceNotConfiguredError(resolved_name)


def set_current_fastpg(name:str) -> None:
    if name not in _FASTPG_REGISTRY:
        raise FastPGInstanceNotConfiguredError(name)
    _CURRENT_FASTPG_NAME.set(name)
