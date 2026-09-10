"""Static consumer checks; Pyright analyzes these functions without running SQL."""
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import assert_type

from fastpg import AsyncQuerySet, DatabaseModel, OnConflict, OrderBy, Q, ReturnType


class User(DatabaseModel):
    id: Optional[int] = None
    name: str
    active: bool = True

    class Meta:
        db_table = "users"
        primary_key = "id"


class Admin(User):
    level: int = 1


async def check_queries(mode: str) -> None:
    assert_type(User.async_queryset, AsyncQuerySet[User, User, None])
    assert_type(Admin.async_queryset, AsyncQuerySet[Admin, Admin, None])
    assert_type(User(name="Ada").async_queryset, AsyncQuerySet[User, User, None])
    assert_type(await AsyncQuerySet(User).get(id=1), User)
    user = await User.async_queryset.get(id=1)
    assert_type(user, User)
    assert_type(user.name, str)
    assert_type(user.id, Optional[int])
    assert_type(await user.save(), bool)
    assert_type(await user.delete(), bool)
    assert_type(await Admin.async_queryset.get(id=1), Admin)
    assert_type(await User.async_queryset.filter(Q(active=True)).using("read").columns("id", "name").order_by(name=OrderBy.ASCENDING).limit(5).offset(0), List[User])
    assert_type(await User.async_queryset.all(), List[User])
    assert_type(await User.async_queryset.count(), int)
    assert_type(await User.async_queryset.filter(id=1).update(name="Grace"), int)
    assert_type(await User.async_queryset.filter(id=1).delete(), int)
    assert_type(await User.async_queryset.create(name="Ada"), User)
    assert_type(await User.async_queryset.bulk_create([{"name": "Ada"}], on_conflict=OnConflict.DO_NOTHING), None)
    assert_type(await User.async_queryset.get_or_create({}, name="Ada"), Tuple[User, bool])
    assert_type(await User.async_queryset.update_or_create({}, name="Ada"), Tuple[User, bool])
    assert_type(await User.async_queryset.execute_raw_query("SELECT * FROM users", {}), List[User])
    assert_type(await User.async_queryset.get(id=1).return_as(ReturnType.DICT), Dict[str, Any])
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).get(id=1), Dict[str, Any])
    assert_type(await User.async_queryset.filter(active=True).return_as(ReturnType.DICT), List[Dict[str, Any]])
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).all(), List[Dict[str, Any]])
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).count(), int)
    assert_type(await User.async_queryset.count().return_as(ReturnType.DICT), int)
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).filter(id=1).update(name="Grace"), int)
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).get(id=1).return_as(ReturnType.MODEL_INSTANCE), User)
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).all().return_as(ReturnType.MODEL_INSTANCE), List[User])
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).create(name="Ada"), User)
    assert_type(await User.async_queryset.get(id=1).return_as(mode), Union[User, Dict[str, Any]])
    assert_type(await User.async_queryset.all().return_as(mode), Union[List[User], List[Dict[str, Any]]])
    assert_type(await User.async_queryset.count().return_as(mode), int)


async def check_pagination() -> None:
    from fastpg import AsyncPaginator, RawQueryAsyncPaginator
    from fastpg.paginator import Page

    paginator = AsyncPaginator(10, User.async_queryset.all())
    assert_type(await paginator.get_page(), Page[User])
    assert_type((await paginator.get_page())["results"], List[User])
    assert_type((await paginator.get_page())["results_paginator"]["has_next"], bool)
    assert_type(await paginator.get_next_page(), Page[User])
    assert_type(await paginator.get_previous_page(), Page[User])
    assert_type(await paginator.get_page(context={"extra": 1}), Dict[str, Any])
    dictionary_page = await AsyncPaginator(10, User.async_queryset.return_as(ReturnType.DICT).all()).get_page()
    assert_type(dictionary_page["results"], List[Dict[str, Any]])

    def names(users: List[User]) -> List[str]:
        return [user.name for user in users]

    serialized = AsyncPaginator(10, User.async_queryset.all(), serializer=names)
    assert_type((await serialized.get_page())["results"], List[str])
    assert_type(await serialized.get_next_page(), Page[str])
    positional = AsyncPaginator(10, User.async_queryset.all(), None, names)
    assert_type((await positional.get_page())["results"], List[str])
    raw = RawQueryAsyncPaginator(10, "SELECT * FROM users", {})
    assert_type((await raw.get_page())["results"], List[Dict[str, Any]])

    def raw_names(rows: List[Dict[str, Any]]) -> List[str]:
        return [str(row["name"]) for row in rows]

    raw_serialized = RawQueryAsyncPaginator(10, "SELECT * FROM users", {}, serializer=raw_names)
    assert_type((await raw_serialized.get_page())["results"], List[str])


async def check_public_api() -> None:
    from fastpg import AsyncRawQuery, ConnectionType, DBConnectionManager, Prefetch, Relation, Transaction, create_fastpg

    instance = create_fastpg(
        databases={"default": {
            "TYPE": ConnectionType.WRITE, "USER": "user", "PASSWORD": "password",
            "DB": "example", "HOST": "localhost", "PORT": 5432,
        }},
        query_logger={"TITLE": "app", "LOG_QUERIES": True},
        db_conn_manager_class=DBConnectionManager,
    )
    assert_type(instance.db_conn_manager, DBConnectionManager)
    related = Relation(User, foreign_field="user_id")
    assert_type(related.related_id_field, str)
    queryset = User.async_queryset.select_related("profile").filter_related(name="Ada").prefetch_related(Prefetch("children", User.async_queryset.all())).filter(id=1).lock_for_update()
    assert_type(await queryset, List[User])
    raw = AsyncRawQuery("SELECT * FROM users")
    assert_type(await raw.fetch({}), List[Dict[str, Any]])
    assert_type(await raw.execute_many([{}]), None)

    @Transaction.decorator()
    async def find_user(user_id: int) -> User:
        return await User.async_queryset.get(id=user_id)

    assert_type(await find_user(1), User)


async def check_rejected_arguments() -> None:
    # Unnecessary ignores fail this check if the library starts accepting these.
    _ = User.async_queryset.limit("5")  # pyright: ignore[reportArgumentType]
    _ = User.async_queryset.columns({"id"})  # pyright: ignore[reportArgumentType]
    _ = User.async_queryset.select_related(["profile"])  # pyright: ignore[reportArgumentType]
    _ = User.async_queryset.order_by(id="SIDEWAYS")  # pyright: ignore[reportArgumentType]
    _ = User(name=123)  # pyright: ignore[reportArgumentType]
    from fastpg import AsyncPaginator
    _ = AsyncPaginator(10, User.async_queryset.count())  # pyright: ignore[reportArgumentType]


async def check_mode_transitions(mode: str) -> None:
    assert_type(await User.async_queryset.all().return_as(mode).return_as(ReturnType.DICT), List[Dict[str, Any]])
    assert_type(await User.async_queryset.return_as(mode).get(id=1), Union[User, Dict[str, Any]])
    assert_type(await User.async_queryset.count().return_as(ReturnType.DICT).filter(id=1), List[Dict[str, Any]])
    assert_type(await User.async_queryset.return_as(ReturnType.DICT).get_or_create({}, name="Ada"), Tuple[Union[Dict[str, Any], User], bool])
