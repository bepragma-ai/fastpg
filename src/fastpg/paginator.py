from __future__ import annotations
from typing import Any, Optional, Callable, Dict, List, Generic, Union, overload, cast
from typing_extensions import TypedDict, TypeVar

from .core import AsyncQuerySet, AsyncRawQuery, DatabaseModel
from .errors import InvalidPageError


_RowT = TypeVar("_RowT", bound=Union[DatabaseModel, Dict[str, Any]], default=Dict[str, Any])
_InputT = TypeVar("_InputT", bound=Union[DatabaseModel, Dict[str, Any]])
_ItemT = TypeVar("_ItemT", default=Any)


class PaginationMetadata(TypedDict):
    number: int
    page_size: int
    has_next: bool
    has_previous: bool
    start_index: Optional[int]
    end_index: Optional[int]


class Page(TypedDict, Generic[_ItemT]):
    results: List[_ItemT]
    results_paginator: PaginationMetadata


class BasePaginator(Generic[_ItemT]):
    """Shared pagination functionality."""

    def __init__(self, page_size: int) -> None:
        self.page: int = 0
        self.page_size = page_size
        self.has_next: bool = True
        self.has_previous: bool = False
        self.start_index: Optional[int] = None
        self.end_index: Optional[int] = None

    @overload
    def get_response(self, data: List[_ItemT], context: None = None) -> Page[_ItemT]: ...

    @overload
    def get_response(self, data: List[_ItemT], context: Optional[Dict[str, Any]]) -> Dict[str, Any]: ...

    def get_response(self, data: List[_ItemT], context: Optional[Dict[str, Any]] = None) -> Union[Page[_ItemT], Dict[str, Any]]:
        object_count = len(data)

        self.has_next = object_count == self.page_size
        self.has_previous = self.page > 1

        if object_count:
            self.start_index = (self.page - 1) * self.page_size
            self.end_index = self.start_index + object_count
        else:
            self.start_index = None
            self.end_index = None

        response: Page[_ItemT] = {
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
            return {**response, **context}
        return response

    @staticmethod
    @overload
    def get_empty_data_response(page:int, page_size:int, context: None = None) -> Page[Any]: ...

    @staticmethod
    @overload
    def get_empty_data_response(page:int, page_size:int, context: Optional[Dict[str, Any]]) -> Dict[str, Any]: ...

    @staticmethod
    def get_empty_data_response(page:int, page_size:int, context: Optional[Dict[str, Any]] = None) -> Union[Page[Any], Dict[str, Any]]:
        response: Page[Any] = {
            "results": [],
            "results_paginator": {
                "number": page,
                "page_size": page_size,
                "has_next": False,
                "has_previous": False,
                "start_index": 0,
                "end_index": 0,
            },
        }
        if context:
            return {**response, **context}
        return response

    @overload
    async def get_page(self, page: int = 1, context: None = None) -> Page[_ItemT]: ...

    @overload
    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = ...) -> Dict[str, Any]: ...

    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = None) -> Union[Page[_ItemT], Dict[str, Any]]:
        raise NotImplementedError

    async def get_next_page(self) -> Page[_ItemT]:
        self.page += 1
        if self.has_next:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])

    async def get_previous_page(self) -> Page[_ItemT]:
        self.page -= 1
        if self.has_previous:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])


class AsyncPaginator(BasePaginator[_ItemT], Generic[_RowT, _ItemT]):
    """Paginator for :class:`AsyncQuerySet` instances."""

    @overload
    def __init__(
        self: AsyncPaginator[_InputT, _InputT], page_size: int,
        queryset: AsyncQuerySet[Any, _InputT, List[_InputT]],
        using: Optional[str] = None, serializer: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self, page_size: int, queryset: AsyncQuerySet[Any, _RowT, List[_RowT]],
        using: Optional[str], serializer: Callable[[List[_RowT]], List[_ItemT]],
    ) -> None: ...

    @overload
    def __init__(
        self, page_size: int, queryset: AsyncQuerySet[Any, _RowT, List[_RowT]],
        using: Optional[str] = None, *, serializer: Callable[[List[_RowT]], List[_ItemT]],
    ) -> None: ...

    def __init__(
        self,
        page_size:int,
        queryset:AsyncQuerySet[Any, _RowT, List[_RowT]],
        using:Optional[str]=None,
        serializer:Optional[Callable[[List[_RowT]], List[_ItemT]]]=None,
    ) -> None:
        super().__init__(page_size=page_size)
        self.queryset = queryset
        self.conn_name = using
        self.serializer = serializer

    @overload
    async def get_page(self, page: int = 1, context: None = None) -> Page[_ItemT]: ...

    @overload
    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = ...) -> Dict[str, Any]: ...

    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = None) -> Union[Page[_ItemT], Dict[str, Any]]:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)

        self.queryset.limit(self.page_size).offset((self.page - 1) * self.page_size)
        if self.conn_name:
            self.queryset.using(self.conn_name)

        records = await self.queryset
        data = self.serializer(records) if self.serializer else cast("List[_ItemT]", records)
        return self.get_response(data=data, context=context)


class RawQueryAsyncPaginator(BasePaginator[_ItemT], Generic[_ItemT]):
    """Paginator for raw SQL queries."""

    @overload
    def __init__(
        self: RawQueryAsyncPaginator[Dict[str, Any]], page_size: int,
        query: str, values: Dict[str, Any], serializer: None = None,
        auto_offset_and_limit: bool = True, using: Optional[str] = None,
    ) -> None: ...

    @overload
    def __init__(
        self, page_size: int, query: str, values: Dict[str, Any],
        serializer: Callable[[List[Dict[str, Any]]], List[_ItemT]],
        auto_offset_and_limit: bool = True, using: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        page_size:int,
        query:str,
        values:Dict[str, Any],
        serializer:Optional[Callable[[List[Dict[str, Any]]], List[_ItemT]]]=None,
        auto_offset_and_limit:bool=True,
        using:Optional[str]=None,
    ) -> None:
        super().__init__(page_size=page_size)
        self.query = query
        self.values = values
        self.serializer = serializer
        self.auto_offset_and_limit = auto_offset_and_limit
        self.conn_name = using
        self.final_query: str = ''

    @overload
    async def get_page(self, page: int = 1, context: None = None) -> Page[_ItemT]: ...

    @overload
    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = ...) -> Dict[str, Any]: ...

    async def get_page(self, page: int = 1, context: Optional[Dict[str, Any]] = None) -> Union[Page[_ItemT], Dict[str, Any]]:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)

        if self.auto_offset_and_limit:
            self.final_query = '{query} LIMIT {page_size:.0f} OFFSET {offset:.0f}'.format(
                query=self.query,
                page_size=self.page_size,
                offset=(self.page - 1) * self.page_size)
        else:
            self.final_query = self.query.format(
                page_size=self.page_size,
                offset=(self.page - 1) * self.page_size)

        raw_query = AsyncRawQuery(query=self.final_query, using=self.conn_name)
        records = await raw_query.fetch(values=self.values)
        data = self.serializer(records) if self.serializer else cast("List[_ItemT]", records)
        return self.get_response(data=data, context=context)
