import pytest
from typing import Optional

from fastpg.constants import ConnectionType, ReturnType
from fastpg.core import DatabaseModel
from fastpg.fastpg import FastPG, register_fastpg
from fastpg.errors import (
    DoesNotExist,
    MultipleRecordsFound,
    NothingToCreateError,
    UnsupportedOperatorError,
)
from fastpg.utils import Relation


class FakeReadConnection:
    def __init__(self, records):
        self.records = records
        self.last_query = None
        self.last_values = None

    async def fetch_all(self, query, values=None):
        self.last_query = query
        self.last_values = values or {}
        return self.records


class FakeWriteConnection:
    def __init__(self, result=1):
        self.result = result
        self.last_query = None
        self.last_values = None

    async def execute(self, query, values=None):
        self.last_query = query
        self.last_values = values or {}
        return self.result

    async def execute_many(self, query, list_of_values):
        self.last_query = query
        self.last_values = list_of_values
        return None


class FakeConnManager:
    def __init__(self, read_conn, write_conn):
        self.read_conn = read_conn
        self.write_conn = write_conn
        self.transaction = None

    def db_for_read(self):
        return self.read_conn

    def db_for_write(self):
        return self.write_conn

    def get_db_conn(self, name):
        if name == "read":
            return self.read_conn
        if name == "write":
            return self.write_conn
        raise KeyError(name)


class Profile(DatabaseModel):
    id: int
    bio: str

    class Meta:
        db_table = "profiles"
        primary_key = "id"


class User(DatabaseModel):
    id: int
    name: str
    profile_id: Optional[int] = None

    class Meta:
        db_table = "users"
        primary_key = "id"
        relations = {
            "profile": Relation(Profile, foreign_field="profile_id", related_name="profile")
        }


def _make_fastpg(read_records=None, write_result=1):
    instance = FastPG(
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
    read_conn = FakeReadConnection(read_records or [])
    write_conn = FakeWriteConnection(write_result)
    instance.db_conn_manager = FakeConnManager(read_conn, write_conn)
    register_fastpg("default", instance)
    return instance


@pytest.mark.asyncio
async def test_get_raises_when_missing():
    _make_fastpg(read_records=[])
    with pytest.raises(DoesNotExist):
        await User.async_queryset.get(id=1)


@pytest.mark.asyncio
async def test_get_returns_single_instance():
    _make_fastpg(read_records=[{"id": 1, "name": "A", "profile_id": None}])
    result = await User.async_queryset.get(id=1)
    assert isinstance(result, User)
    assert result.name == "A"


@pytest.mark.asyncio
async def test_get_raises_when_multiple():
    _make_fastpg(read_records=[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    with pytest.raises(MultipleRecordsFound):
        await User.async_queryset.get(id__in=[1, 2])


@pytest.mark.asyncio
async def test_filter_returns_dicts_with_return_as():
    _make_fastpg(read_records=[{"id": 1, "name": "A"}])
    result = await User.async_queryset.filter(id=1).return_as(ReturnType.DICT)
    assert result == [{"id": 1, "name": "A"}]


@pytest.mark.asyncio
async def test_count_returns_value():
    _make_fastpg(read_records=[{"count": 3}])
    result = await User.async_queryset.count()
    assert result == 3


@pytest.mark.asyncio
async def test_update_requires_where_clause():
    _make_fastpg()
    queryset = User.async_queryset.update(name="Bob")
    assert queryset.where_conditions == ""


@pytest.mark.asyncio
async def test_update_renders_jsonb_and_arithmetic_ops():
    instance = _make_fastpg()
    queryset = User.async_queryset.filter(id=1).update(
        score__add=1,
        data__jsonb={"a": 1},
        info__jsonb_set__key="value",
    )
    updated = await queryset
    assert updated == 1
    query = instance.db_conn_manager.write_conn.last_query
    values = instance.db_conn_manager.write_conn.last_values
    assert "score=score + 1" in query
    assert "data=:set_data" in query
    assert "info=jsonb_set(info, '{key}', :set_key, true)" in query
    assert "set_data" in values
    assert "set_key" in values


@pytest.mark.asyncio
async def test_update_rejects_invalid_operator():
    _make_fastpg()
    with pytest.raises(UnsupportedOperatorError):
        User.async_queryset.filter(id=1).update(name__bogus="x")


@pytest.mark.asyncio
async def test_delete_requires_where_clause():
    _make_fastpg()
    queryset = User.async_queryset.delete()
    assert queryset.where_conditions == ""


@pytest.mark.asyncio
async def test_bulk_create_requires_values():
    _make_fastpg()
    with pytest.raises(NothingToCreateError):
        await User.async_queryset.bulk_create(values=[])


@pytest.mark.asyncio
async def test_select_related_hydrates_related_object():
    records = [
        {
            "t_id": 1,
            "t_name": "A",
            "t_profile_id": 10,
            "r_id": 10,
            "r_bio": "bio",
        }
    ]
    _make_fastpg(read_records=records)
    result = await User.async_queryset.select_related("profile").get(id=1)
    assert isinstance(result.profile, Profile)
    assert result.profile.bio == "bio"
