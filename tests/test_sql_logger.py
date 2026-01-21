import logging

import pytest

from fastpg.constants import ConnectionType
from fastpg.fastpg import create_fastpg
from fastpg.utils import async_sql_logger


class DummyConn:
    def __init__(self):
        self.conn_name = "read"
        self.conn_type = ConnectionType.READ


@pytest.mark.asyncio
async def test_async_sql_logger_emits_logs(caplog):
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
        },
        query_logger={"TITLE": "TEST", "LOG_QUERIES": True},
    )

    @async_sql_logger
    async def _run(conn, query):
        return "ok"

    caplog.set_level(logging.INFO, logger="fastpg.utils")
    result = await _run(DummyConn(), query="SELECT 1")
    assert result == "ok"
    assert any("TEST_QUERY" in record.message for record in caplog.records)
