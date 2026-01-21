import pytest

from fastpg.constants import ConnectionType
from fastpg.fastpg import create_fastpg
from fastpg.db import AsyncPostgresDBConnection


class FakeTransaction:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class FakeDatabase:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.connected = False
        self.executed = []
        self.transaction_obj = FakeTransaction()

    async def connect(self):
        if self.should_fail:
            raise RuntimeError("connect failed")
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def fetch_one(self, query, values=None):
        return {"query": query, "values": values or {}}

    async def fetch_all(self, query, values=None):
        return [{"query": query, "values": values or {}}]

    async def execute(self, query, values=None):
        self.executed.append(("execute", query, values or {}))
        return 1

    async def execute_many(self, query, values=None):
        self.executed.append(("execute_many", query, values or []))
        return 1

    async def transaction(self):
        return self.transaction_obj


@pytest.fixture(autouse=True)
def _fastpg_instance():
    create_fastpg(
        databases={
            "read": {
                "TYPE": ConnectionType.READ,
                "USER": "user",
                "PASSWORD": "pass",
                "DB": "db",
                "HOST": "localhost",
                "PORT": 5432,
            },
            "write": {
                "TYPE": ConnectionType.WRITE,
                "USER": "user",
                "PASSWORD": "pass",
                "DB": "db",
                "HOST": "localhost",
                "PORT": 5432,
            },
        }
    )
    yield


@pytest.mark.asyncio
async def test_connect_sets_transaction_for_write(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr("fastpg.db.Database", lambda *args, **kwargs: fake_db)
    conn = AsyncPostgresDBConnection(
        conn_name="write",
        conn_type=ConnectionType.WRITE,
        db_uri="postgresql://localhost/db",
    )
    await conn.connect()
    assert conn.database is fake_db
    assert conn.transaction == fake_db.transaction


@pytest.mark.asyncio
async def test_execute_commits_on_success(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr("fastpg.db.Database", lambda *args, **kwargs: fake_db)
    conn = AsyncPostgresDBConnection(
        conn_name="write",
        conn_type=ConnectionType.WRITE,
        db_uri="postgresql://localhost/db",
    )
    await conn.connect()
    result = await conn.execute("SELECT 1", values={"id": 1})
    assert result == 1
    assert fake_db.transaction_obj.committed is True
    assert fake_db.transaction_obj.rolled_back is False


@pytest.mark.asyncio
async def test_execute_rolls_back_on_failure(monkeypatch):
    class FailingDatabase(FakeDatabase):
        async def execute(self, query, values=None):
            raise RuntimeError("boom")

    fake_db = FailingDatabase()
    monkeypatch.setattr("fastpg.db.Database", lambda *args, **kwargs: fake_db)
    conn = AsyncPostgresDBConnection(
        conn_name="write",
        conn_type=ConnectionType.WRITE,
        db_uri="postgresql://localhost/db",
    )
    await conn.connect()
    with pytest.raises(RuntimeError):
        await conn.execute("SELECT 1", values={"id": 1})
    assert fake_db.transaction_obj.rolled_back is True


@pytest.mark.asyncio
async def test_execute_many_commits(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr("fastpg.db.Database", lambda *args, **kwargs: fake_db)
    conn = AsyncPostgresDBConnection(
        conn_name="write",
        conn_type=ConnectionType.WRITE,
        db_uri="postgresql://localhost/db",
    )
    await conn.connect()
    await conn.execute_many("INSERT", list_of_values=[{"id": 1}])
    assert fake_db.transaction_obj.committed is True
