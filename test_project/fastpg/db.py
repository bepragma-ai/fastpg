import os
import asyncio
from typing import Optional, Dict, List
from databases import Database

from .utils import async_sql_logger
from .print import print_red


# MAIN DB POSTGRES READ SYNC
POSTGRES_READ_USER = os.environ.get("POSTGRES_READ_USER")
POSTGRES_READ_PASSWORD = os.environ.get("POSTGRES_READ_PASSWORD")
POSTGRES_READ_DB = os.environ.get("POSTGRES_READ_DB")
POSTGRES_READ_HOST = os.environ.get("POSTGRES_READ_HOST")
POSTGRES_READ_PORT = os.environ.get("POSTGRES_READ_PORT")

# MAIN DB POSTGRES WRITE SYNC
POSTGRES_WRITE_USER = os.environ.get("POSTGRES_WRITE_USER")
POSTGRES_WRITE_PASSWORD = os.environ.get("POSTGRES_WRITE_PASSWORD")
POSTGRES_WRITE_DB = os.environ.get("POSTGRES_WRITE_DB")
POSTGRES_WRITE_HOST = os.environ.get("POSTGRES_WRITE_HOST")
POSTGRES_WRITE_PORT = os.environ.get("POSTGRES_WRITE_PORT")


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

    def __init__(self, conn_type: str, max_retries: int = 3, retry_delay: int = 2) -> None:
        self.conn_type = conn_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.database: Optional[Database] = None

    async def connect(self) -> None:
        """Establish a connection to the database with retry logic."""

        retries = 0
        while retries < self.max_retries:
            try:
                if self.conn_type == "READ":
                    self.database = Database(
                        f"postgresql+asyncpg://{POSTGRES_READ_USER}:{POSTGRES_READ_PASSWORD}@{POSTGRES_READ_HOST}:{POSTGRES_READ_PORT}/{POSTGRES_READ_DB}",
                        min_size=2,
                        max_size=5,
                        statement_cache_size=0,
                    )
                else:
                    self.database = Database(
                        f"postgresql+asyncpg://{POSTGRES_WRITE_USER}:{POSTGRES_WRITE_PASSWORD}@{POSTGRES_WRITE_HOST}:{POSTGRES_WRITE_PORT}/{POSTGRES_WRITE_DB}",
                        min_size=2,
                        max_size=5,
                        statement_cache_size=0,
                    )
                await self.database.connect()
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
    async def execute(self, query: str, values: Optional[Dict] = None, transaction=None):
        """Execute a query with optional values.

        When a ``transaction`` is provided the caller controls commit/rollback;
        otherwise a new transaction is created for the single execution.
        """

        values = values or {}

        # If caller passed a transaction, execute within that context without
        # creating a nested transaction or auto-committing.
        if transaction is not None:
            return await self.database.execute(query=query, values=values)

        transaction_ctx = await self.database.transaction()
        try:
            result = await self.database.execute(query=query, values=values)
        except Exception as e:
            await transaction_ctx.rollback()
            raise e
        else:
            await transaction_ctx.commit()
        return result

    @async_sql_logger
    async def execute_many(self, query: str, list_of_values: List[Dict], transaction=None):
        """Execute a query for multiple sets of values.

        When a ``transaction`` is provided the caller controls commit/rollback;
        otherwise a new transaction is created for the bulk execution.
        """

        if transaction is not None:
            return await self.database.execute_many(query=query, values=list_of_values)

        transaction_ctx = await self.database.transaction()
        try:
            result = await self.database.execute_many(query=query, values=list_of_values)
        except Exception as e:
            await transaction_ctx.rollback()
            raise e
        else:
            await transaction_ctx.commit()
        return result

    async def transaction(self):
        """Return a database transaction object managed by the caller."""

        if not self.database:
            raise RuntimeError("Database connection is not initialized")
        return await self.database.transaction()

    async def close(self) -> None:
        """Close the database connection if it exists."""

        if self.database:
            await self.database.disconnect()


ASYNC_DB_READ = AsyncPostgresDB(conn_type='READ')
ASYNC_DB_WRITE = AsyncPostgresDB(conn_type='WRITE')
