import os
import asyncio
import random
from typing import Optional, Dict, List, Any
from databases import Database

from .constants import ConnectionType

from .utils import async_sql_logger
from .print import print_red, print_green


class AsyncPostgresDB:
    """Asynchronous PostgreSQL database wrapper.

    Parameters
    ----------
    conn_type: str
        Specifies whether the connection is for ``READ`` or ``WRITE``.
    max_retries: int, optional
        Number of retry attempts before failing to connect.
    retry_delay: int, optional
        Delay in seconds between retries.
    """

    def __init__(self, conn_type: ConnectionType, db_uri: str, max_retries: int = 3, retry_delay: int = 2) -> None:
        self.conn_type = conn_type
        self.db_uri = db_uri
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.database: Optional[Database] = None
        self.transaction = None

    async def connect(self) -> None:
        """Establish a connection to the database with retry logic."""

        retries = 0
        while retries < self.max_retries:
            try:
                if self.conn_type == ConnectionType.READ:
                    self.database = Database(
                        self.db_uri,
                        min_size=2,
                        max_size=5,
                        statement_cache_size=0,
                    )
                else:
                    self.database = Database(
                        self.db_uri,
                        min_size=2,
                        max_size=5,
                        statement_cache_size=0,
                    )
                await self.database.connect()
                self.transaction = self.database.transaction
                return
            except Exception as e:  # pragma: no cover - network failures
                print_red(f"Async connection failed (attempt {retries + 1}): {e}")
                retries += 1
                await asyncio.sleep(self.retry_delay)
        raise Exception("Failed to connect to the database after multiple retries.")
    
    @async_sql_logger
    async def fetch_one(self, query: str, values: Optional[Dict] = None):
        """Fetch a single record from the database."""

        values = values or {}
        return await self.database.fetch_one(query=query, values=values)
    
    @async_sql_logger
    async def fetch_all(self, query: str, values: Optional[Dict] = None):
        """Fetch multiple records from the database."""

        values = values or {}
        return await self.database.fetch_all(query=query, values=values)

    @async_sql_logger
    async def execute(self, query: str, values: Optional[Dict] = None):
        """Execute a query with optional values inside a transaction."""

        values = values or {}
        transaction = await self.database.transaction()
        try:
            result = await self.database.execute(query=query, values=values)
        except Exception as e:
            await transaction.rollback()
            raise e
        else:
            await transaction.commit()
        return result

    @async_sql_logger
    async def execute_many(self, query: str, list_of_values: List[Dict]):
        """Execute a query for multiple sets of values inside a transaction."""

        transaction = await self.database.transaction()
        try:
            result = await self.database.execute_many(query=query, values=list_of_values)
        except Exception as e:
            await transaction.rollback()
            raise e
        else:
            await transaction.commit()
        return result

    async def close(self) -> None:
        """Close the database connection if it exists."""

        if self.database:
            await self.database.disconnect()


class ConnectionManager:
    """
    Parameters
    ----------
    databases: dict
        Dictionary of database connections. E.g.

        {
            'default': {
                'TYPE': ConnectionType.WRITE,
                'USER': '',
                'PASSWORD': '',
                'DB': '',
                'HOST': '',
                'PORT': '',
            },
            'replica_1': {
                'TYPE': ConnectionType.READ,
                'USER': '',
                'PASSWORD': '',
                'DB': '',
                'HOST': '',
                'PORT': '',
            }
        }
    """

    def __init__(self):
        self.databases = {}
        self.connections = {}
        self.read_conn_names = []
        self.write_conn_name = None
    
    def __create_connections(self) -> None:
        for conn_name in self.databases:
            config = self.databases[conn_name]

            conn_type = config['TYPE']
            user = config['USER']
            password = config['PASSWORD']
            db = config['DB']
            host = config['HOST']
            port = config['PORT']

            self.connections[conn_name] = AsyncPostgresDB(
                conn_type=conn_type,
                db_uri=f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}")
            
            if conn_type == ConnectionType.READ:
                self.read_conn_names.append(conn_name)
            else:
                if self.write_conn_name is None:
                    self.write_conn_name = conn_name
                else:
                    raise ValueError('Multiple write connections are not allowed')
            
        if len(self.read_conn_names) == 0:
            raise ValueError('At least one read connection must be provided')
    
    def set_databases(self, databases:Dict[str, Any]) -> None:
        self.databases = databases
        self.__create_connections()

    async def connect_all(self) -> None:
        for conn_name in self.connections:
            await self.connections[conn_name].connect()
            print_green(f'"{conn_name}" successfully connected...')
    
    async def close_all(self) -> None:
        for conn_name in self.connections:
            await self.connections[conn_name].close()
            print_green(f'"{conn_name}" successfully closed...')

    def db_for_read(self):
        conn_name = random.choice(self.read_conn_names)
        return self.connections[conn_name]

    def db_for_write(self):
        return self.connections[self.write_conn_name]


CONNECTION_MANAGER = ConnectionManager()


# # MAIN DB POSTGRES READ SYNC
# POSTGRES_READ_USER = os.environ.get("POSTGRES_READ_USER")
# POSTGRES_READ_PASSWORD = os.environ.get("POSTGRES_READ_PASSWORD")
# POSTGRES_READ_DB = os.environ.get("POSTGRES_READ_DB")
# POSTGRES_READ_HOST = os.environ.get("POSTGRES_READ_HOST")
# POSTGRES_READ_PORT = os.environ.get("POSTGRES_READ_PORT")

# # MAIN DB POSTGRES WRITE SYNC
# POSTGRES_WRITE_USER = os.environ.get("POSTGRES_WRITE_USER")
# POSTGRES_WRITE_PASSWORD = os.environ.get("POSTGRES_WRITE_PASSWORD")
# POSTGRES_WRITE_DB = os.environ.get("POSTGRES_WRITE_DB")
# POSTGRES_WRITE_HOST = os.environ.get("POSTGRES_WRITE_HOST")
# POSTGRES_WRITE_PORT = os.environ.get("POSTGRES_WRITE_PORT")


# ASYNC_DB_READ = AsyncPostgresDB(conn_type=ConnectionType.READ, db_uri=f"postgresql+asyncpg://{POSTGRES_READ_USER}:{POSTGRES_READ_PASSWORD}@{POSTGRES_READ_HOST}:{POSTGRES_READ_PORT}/{POSTGRES_READ_DB}")
# ASYNC_DB_WRITE = AsyncPostgresDB(conn_type=ConnectionType.WRITE, db_uri=f"postgresql+asyncpg://{POSTGRES_WRITE_USER}:{POSTGRES_WRITE_PASSWORD}@{POSTGRES_WRITE_HOST}:{POSTGRES_WRITE_PORT}/{POSTGRES_WRITE_DB}")
