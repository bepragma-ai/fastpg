import os
import time
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from databases import Database

from .utils import async_sql_logger
from .utils import sync_sql_logger

from app.utils.color_print import print_green, print_red, print_yellow


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


class SyncPostgresDB:
    def __init__(self, conn_type:str, max_retries:int=3, retry_delay:int=2) -> None:
        self.conn_type = conn_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = None

    def connect(self):
        self.close()
        retries = 0
        while retries < self.max_retries:
            try:
                if self.conn_type == 'READ':
                    self.conn = psycopg2.connect(
                        host=POSTGRES_READ_HOST,
                        database=POSTGRES_READ_DB,
                        user=POSTGRES_READ_USER,
                        password=POSTGRES_READ_PASSWORD,
                        port=POSTGRES_READ_PORT)
                else:
                    self.conn = psycopg2.connect(
                        host=POSTGRES_WRITE_HOST,
                        database=POSTGRES_WRITE_DB,
                        user=POSTGRES_WRITE_USER,
                        password=POSTGRES_WRITE_PASSWORD,
                        port=POSTGRES_WRITE_PORT)
                return
            except psycopg2.OperationalError as e:
                print_red(f'Connection failed (attempt {retries + 1}): {e}')
                retries += 1
                time.sleep(self.retry_delay)
        raise Exception('Failed to connect to the database after multiple retries.')

    def get_cursor(self):
        if self.conn is None or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)

    @sync_sql_logger
    def fetch_one(self, query:str, values:dict):
        result = None
        try:
            with self.get_cursor() as cur:
                cur.execute(query, values)
                result = cur.fetchone()
        except psycopg2.OperationalError:
            print_yellow('Connection lost. Reconnecting...')
            self.connect()
            return self.fetch_one(query, values)
        except psycopg2.Error as e:
            raise e
        return result
    
    @sync_sql_logger
    def fetch_all(self, query:str, values:dict):
        result = None
        try:
            with self.get_cursor() as cur:
                cur.execute(query, values)
                result = cur.fetchall()
        except psycopg2.OperationalError:
            print_yellow('Connection lost. Reconnecting...')
            self.connect()
            return self.fetch_one(query, values)
        except psycopg2.Error as e:
            raise e
        return result

    @sync_sql_logger
    def execute(self, query:str, values:dict):
        result = None
        try:
            with self.get_cursor() as cur:
                cur.execute(query, values)
                self.conn.commit()
                result = cur.fetchall()
        except psycopg2.OperationalError:
            print_yellow('Connection lost. Reconnecting...')
            self.connect()
            return self.execute(query, values)
        except psycopg2.Error as e:
            self.conn.rollback()
            raise e
        return result
    
    @sync_sql_logger
    def execute_many(self, query, list_of_values):
        result = None
        try:
            with self.get_cursor() as cur:
                cur.executemany(query, list_of_values)
                self.conn.commit()
                result = cur.fetchall()
        except psycopg2.OperationalError:
            print_yellow('Connection lost. Reconnecting...')
            self.connect()
            result = self.executemany(query, list_of_values)
        except psycopg2.Error as e:
            self.conn.rollback()
            raise e
        return result

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()


ASYNC_CUSTOMERS_DB_READ = AsyncPostgresDB(conn_type='READ')
ASYNC_CUSTOMERS_DB_WRITE = AsyncPostgresDB(conn_type='WRITE')

SYNC_SEGMENTS_DB_READ = SyncPostgresDB(conn_type='READ')
SYNC_SEGMENTS_DB_WRITE = SyncPostgresDB(conn_type='WRITE')
