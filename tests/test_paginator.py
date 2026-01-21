import pytest

from fastpg.paginator import AsyncPaginator, BasePaginator, RawQueryAsyncPaginator
from fastpg.errors import InvalidPageError


class FakeQuerySet:
    def __init__(self, data):
        self.data = data
        self.limit_value = None
        self.offset_value = None

    def limit(self, limit_value):
        self.limit_value = limit_value
        return self

    def offset(self, offset_value):
        self.offset_value = offset_value
        return self

    def __await__(self):
        async def _inner():
            return self.data

        return _inner().__await__()


def test_base_paginator_response_metadata():
    paginator = BasePaginator(page_size=2)
    paginator.page = 1
    response = paginator.get_response(data=[{"id": 1}])
    meta = response["results_paginator"]
    assert meta["has_next"] is False
    assert meta["has_previous"] is False
    assert meta["start_index"] == 0
    assert meta["end_index"] == 1


@pytest.mark.asyncio
async def test_async_paginator_page_flow():
    queryset = FakeQuerySet([{"id": 1}, {"id": 2}])
    paginator = AsyncPaginator(page_size=2, queryset=queryset)
    response = await paginator.get_page(page=1)
    assert response["results"] == [{"id": 1}, {"id": 2}]
    assert queryset.limit_value == 2
    assert queryset.offset_value == 0


@pytest.mark.asyncio
async def test_async_paginator_invalid_page():
    paginator = AsyncPaginator(page_size=2, queryset=FakeQuerySet([]))
    with pytest.raises(InvalidPageError):
        await paginator.get_page(page=0)


@pytest.mark.asyncio
async def test_raw_query_paginator_serializer(monkeypatch):
    class FakeRawQuery:
        def __init__(self, query):
            self.query = query

        async def fetch(self, values):
            return [{"id": 1}]

    monkeypatch.setattr("fastpg.paginator.AsyncRawQuery", FakeRawQuery)
    paginator = RawQueryAsyncPaginator(
        page_size=1,
        query="SELECT * FROM items",
        values={},
        serializer=lambda rows: [{"id": r["id"], "ok": True} for r in rows],
    )
    response = await paginator.get_page(page=1)
    assert response["results"] == [{"id": 1, "ok": True}]
