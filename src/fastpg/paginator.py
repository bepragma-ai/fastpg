from typing import Any, Optional, Callable, Dict

from .constants import ReturnType
from .core import AsyncQuerySet, AsyncRawQuery
from .errors import InvalidPageError


class BasePaginator:
    """Shared pagination functionality."""

    def __init__(self, page_size: int) -> None:
        self.page = 0
        self.page_size = page_size
        self.has_next = True
        self.has_previous = False
        self.start_index: Optional[int] = None
        self.end_index: Optional[int] = None

    def get_response(self, data: list, context: Optional[Dict] = None) -> dict:
        object_count = len(data)

        self.has_next = object_count == self.page_size
        self.has_previous = self.page > 1

        if object_count:
            self.start_index = (self.page - 1) * self.page_size
            self.end_index = self.start_index + object_count
        else:
            self.start_index = None
            self.end_index = None

        response = {
            "results": data,
            "results_paginator": {
                "number": self.page,
                "page_size": self.page_size,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
                "start_index": self.start_index,
                "end_index": self.end_index,
            },
        }
        if context:
            response = {**response, **context}
        return response

    async def get_next_page(self) -> dict:
        self.page += 1
        if self.has_next:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])

    async def get_previous_page(self) -> dict:
        self.page -= 1
        if self.has_previous:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])


class AsyncPaginator(BasePaginator):
    """Paginator for :class:`AsyncQuerySet` instances."""

    def __init__(self, page_size: int, queryset: AsyncQuerySet) -> None:
        super().__init__(page_size=page_size)
        self.queryset = queryset

    async def get_page(self, page: int = 1, context: Optional[Dict] = None) -> dict:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)

        self.queryset.limit(self.page_size).offset((self.page - 1) * self.page_size)

        if isinstance(self.queryset, AsyncQuerySet):
            data = await self.queryset.return_as(return_type=ReturnType.DICT)
        else:
            data = await self.queryset

        return self.get_response(data=data, context=context)


class RawQueryAsyncPaginator(BasePaginator):
    """Paginator for raw SQL queries."""

    def __init__(
        self,
        page_size: int,
        query: str,
        values: Dict[str, Any],
        serializer: Optional[Callable] = None,
    ):
        super().__init__(page_size=page_size)
        self.query = query
        self.values = values
        self.serializer = serializer

    async def get_page(self, page: int = 1, context: Optional[Dict] = None) -> dict:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)

        _query = self.query.format(limit=self.page_size, offset=(self.page - 1) * self.page_size)

        raw_query = AsyncRawQuery(query=_query, values=self.values)
        records = await raw_query.fetch()
        if self.serializer:
            records = self.serializer(records)

        return self.get_response(data=records, context=context)

