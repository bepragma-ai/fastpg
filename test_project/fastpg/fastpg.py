from typing import Dict, Any
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

    def __init__(self):
        self.tz_name = 'UTC'
        self.TZ = None
        self.log_title = ''
        self.log_db_queries = False
        self.db_conn_manager:DBConnectionManager = None

    def configure(
            self,
            databases:Dict[str, Dict[str, str]]=None,
            fastpg_tz:str='UTC',
            query_logger:Dict[str, Any]=None
        ):
        if query_logger:
            self.log_title = query_logger['TITLE']
            self.log_db_queries = query_logger['LOG_QUERIES']
        self.tz_name = fastpg_tz
        self.__get_timezone()

        self.db_conn_manager = DBConnectionManager(databases or {})
    
    def __get_timezone(self) -> None:
        """Return the configured timezone.

        The timezone name is read from the ``FASTPG_TZ`` environment variable. If the
        variable is not set or invalid, UTC is used.
        """
        try:
            self.TZ = pytz.timezone(self.tz_name)
        except pytz.UnknownTimeZoneError:
            self.TZ = pytz.UTC


FAST_PG = FastPG()
