from typing import Any

from .constants import ReturnTypes
from .core import AsyncQuerySet
from .core import AsyncRawQuery
from .errors import InvalidPageError

from app.utils.color_print import print_green, print_yellow, print_red


class AsyncPaginator:

    def __init__(
        self,
        page_size:int,
        queryset:AsyncQuerySet,
    ) -> None:
        self.queryset = queryset
        self.page = 0
        self.page_size = page_size
        self.has_next = True
        self.has_previous = False
        self.start_index = None
        self.end_index = None

    def get_response(self, data:list, context:dict=None) -> dict:
        object_count = len(data)

        self.has_next = object_count == self.page_size
        self.has_previous = self.page > 1

        if object_count:
            self.start_index = (self.page - 1) * self.page_size
            self.end_index = (self.page - 1) * self.page_size + object_count
        else:
            self.start_index = None
            self.end_index = None

        data = {
            'results': data,
            'results_paginator': {
                'number': self.page,
                'page_size': self.page_size,
                'has_next': self.has_next,
                'has_previous': self.has_previous,
                'start_index': self.start_index,
                'end_index': self.end_index
            }
        }
        if context:
            data = {**data, **context}
        return data
    
    async def get_page(self, page:int=1, context:dict=None) -> dict:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)
        
        self.queryset.limit(self.page_size).offset((self.page - 1) * self.page_size)
        
        if isinstance(self.queryset, AsyncQuerySet):
            data = await self.queryset.return_as(return_type=ReturnTypes.DICT)
        else:
            data = await self.queryset

        return self.get_response(data=data, context=context)

    async def get_next_page(self) -> dict:
        self.page = self.page + 1
        if self.has_next:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])

    async def get_previous_page(self) -> dict:
        self.page = self.page - 1
        if self.has_previous:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])


class RawQueryAsyncPaginator:

    def __init__(
        self,
        page_size:int,
        query:str,
        values:dict[str, Any],
        serializer:callable=None
    ):
        self.query = query
        self.values = values

        self.page = 0
        self.page_size = page_size
        self.has_next = True
        self.has_previous = False
        self.start_index = None
        self.end_index = None

        self.serializer = serializer
    
    def get_response(self, records:list, context:dict=None) -> dict:
        object_count = len(records)

        self.has_next = object_count == self.page_size
        self.has_previous = self.page > 1

        if object_count:
            self.start_index = (self.page - 1) * self.page_size
            self.end_index = (self.page - 1) * self.page_size + object_count
        else:
            self.start_index = None
            self.end_index = None
        
        data = {
            'results': records,
            'results_paginator': {
                'number': self.page,
                'page_size': self.page_size,
                'has_next': self.has_next,
                'has_previous': self.has_previous,
                'start_index': self.start_index,
                'end_index': self.end_index
            }
        }
        if context:
            data = {**data, **context}
        return data
    
    async def get_page(self, page:int=1, context:dict=None) -> dict:
        self.page = page
        if self.page < 1:
            raise InvalidPageError(page=self.page)
        
        _query = self.query.format(limit=self.page_size, offset=(self.page - 1) * self.page_size)

        raw_query = AsyncRawQuery(query=_query, values=self.values)
        records = await raw_query.fetch()
        if self.serializer:
            records = self.serializer(records)

        return self.get_response(records=records, context=context)
        
    async def get_next_page(self) -> dict:
        self.page = self.page + 1
        if self.has_next:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])
    
    async def get_previous_page(self) -> dict:
        self.page = self.page - 1
        if self.has_previous:
            return await self.get_page(page=self.page)
        return self.get_response(data=[])
