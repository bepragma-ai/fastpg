import pytest

from fastpg.constants import ConnectionType
from fastpg.fastpg import DBConnectionManager
from fastpg.errors import (
    InvalidConnectionNameError,
    MultipleWriteConnectionsError,
    ReadConnectionNotAvailableError,
)


def test_requires_at_least_one_read_connection():
    config = {
        "write": {
            "TYPE": ConnectionType.WRITE,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        }
    }
    with pytest.raises(ReadConnectionNotAvailableError):
        DBConnectionManager(config)


def test_rejects_multiple_write_connections():
    config = {
        "write_primary": {
            "TYPE": ConnectionType.WRITE,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
        "write_replica": {
            "TYPE": ConnectionType.WRITE,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
        "read": {
            "TYPE": ConnectionType.READ,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
    }
    with pytest.raises(MultipleWriteConnectionsError):
        DBConnectionManager(config)


def test_get_db_conn_raises_on_invalid_name():
    config = {
        "read": {
            "TYPE": ConnectionType.READ,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
    }
    manager = DBConnectionManager(config)
    with pytest.raises(InvalidConnectionNameError):
        manager.get_db_conn("missing")
