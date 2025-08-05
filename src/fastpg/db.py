import os
import asyncio
from databases import Database

from .utils import async_sql_logger


# MAIN DB POSTGRES READ SYNC
POSTGRES_READ_USER = os.environ.get("POSTGRES_USER")
POSTGRES_READ_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_READ_DB = os.environ.get("POSTGRES_DB")
POSTGRES_READ_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_READ_PORT = os.environ.get("POSTGRES_PORT")

# MAIN DB POSTGRES WRITE SYNC
POSTGRES_WRITE_USER = os.environ.get("POSTGRES_USER")
POSTGRES_WRITE_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_WRITE_DB = os.environ.get("POSTGRES_DB")
POSTGRES_WRITE_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_WRITE_PORT = os.environ.get("POSTGRES_PORT")


class AsyncPostgresDB:
    def __init__(self, conn_type:str, max_retries:int=3, retry_delay:int=2) -> None:
        self.conn_type = conn_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.database = None

    async def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                if self.conn_type == 'READ':
                    self.database = Database(
                        f"postgresql+asyncpg://{POSTGRES_READ_USER}:{POSTGRES_READ_PASSWORD}@{POSTGRES_READ_HOST}:{POSTGRES_READ_PORT}/{POSTGRES_READ_DB}",
                        min_size=2, max_size=5, statement_cache_size=0)
                else:
                    self.database = Database(
                        f"postgresql+asyncpg://{POSTGRES_WRITE_USER}:{POSTGRES_WRITE_PASSWORD}@{POSTGRES_WRITE_HOST}:{POSTGRES_WRITE_PORT}/{POSTGRES_WRITE_DB}",
                        min_size=2, max_size=5, statement_cache_size=0)
                await self.database.connect()
                return
            except Exception as e:
                print(f"Async connection failed (attempt {retries + 1}): {e}")
                retries += 1
                await asyncio.sleep(self.retry_delay)
        raise Exception("Failed to connect to the database after multiple retries.")
    
    @async_sql_logger
    async def fetch_one(self, query:str, values=dict):
        return await self.database.fetch_one(query=query, values=values)
    
    @async_sql_logger
    async def fetch_all(self, query:str, values=dict):
        return await self.database.fetch_all(query=query, values=values)

    @async_sql_logger
    async def execute(self, query:str, values=dict):
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
    async def execute_many(self, query, list_of_values):
        transaction = await self.database.transaction()
        try:
            result = await self.database.execute_many(query=query, values=list_of_values)
        except Exception as e:
            await transaction.rollback()
            raise e
        else:
            await transaction.commit()
        return result

    async def close(self):
        if self.database:
            await self.database.disconnect()


ASYNC_CUSTOMERS_DB_READ = AsyncPostgresDB(conn_type='READ')
ASYNC_CUSTOMERS_DB_WRITE = AsyncPostgresDB(conn_type='WRITE')
