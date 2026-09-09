"""Run: cd test_project && bash docker.sh exec app python < check_queryset_regressions.py

Uses session-local temporary tables and rolls back every transaction.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastpg import ConnectionType, DatabaseModel, JsonData, OnConflict, Prefetch, Q, Relation, ReturnType, create_fastpg
from fastpg.fastpg import set_current_fastpg
from fastpg.paginator import AsyncPaginator
from fastpg.errors import DatabaseError


class Profile(DatabaseModel):
    id: int
    bio: str

    class Meta:
        db_table = 'pg_temp.fastpg_review_profiles'
        primary_key = 'id'


class User(DatabaseModel):
    id: int
    name: str
    profile_id: int

    class Meta:
        db_table = 'pg_temp.fastpg_review_users'
        primary_key = 'id'
        relations = {'profile': Relation(Profile, 'profile_id')}


class Post(DatabaseModel):
    id: int
    user_id: int

    class Meta:
        db_table = 'pg_temp.fastpg_review_posts'
        primary_key = 'id'
        relations = {'user': Relation(User, 'user_id')}


class Values(DatabaseModel):
    id: int
    properties: JsonData
    other: JsonData
    expires: datetime

    class Meta:
        db_table = 'pg_temp.fastpg_review_values'
        primary_key = 'id'


def instance(name):
    primary = {
        key: os.environ['POSTGRES_WRITE_' + key]
        for key in ('USER', 'PASSWORD', 'DB', 'HOST', 'PORT')
    }
    return create_fastpg(name=name, databases={
        'default': {**primary, 'TYPE': ConnectionType.WRITE},
        'read': {**primary, 'TYPE': ConnectionType.READ},
    })


async def fixtures(conn, label):
    for statement in (
        'CREATE TEMP TABLE fastpg_review_profiles (id integer PRIMARY KEY, bio text) ON COMMIT DROP',
        'CREATE TEMP TABLE fastpg_review_users (id integer PRIMARY KEY, name text, profile_id integer) ON COMMIT DROP',
        'CREATE TEMP TABLE fastpg_review_posts (id integer PRIMARY KEY, user_id integer) ON COMMIT DROP',
        'CREATE TEMP TABLE fastpg_review_values (id integer PRIMARY KEY, properties jsonb, other jsonb, expires timestamptz) ON COMMIT DROP',
        "INSERT INTO pg_temp.fastpg_review_values VALUES (1, '{}', '{}', '2026-09-09T00:00:00Z')",
        "INSERT INTO pg_temp.fastpg_review_profiles VALUES (10, 'keep'), (20, 'exclude')",
        'INSERT INTO pg_temp.fastpg_review_posts VALUES (100, 1), (200, 2)',
    ):
        await conn.execute(statement)
    await conn.execute(
        'INSERT INTO pg_temp.fastpg_review_users VALUES (1, :name, 10), (2, :name, 20)',
        {'name': label},
    )


def users():
    return User.async_queryset.using('default')


def related_users():
    return users().select_related('profile').filter(id__gt=0).filter_related(profile__bio='keep')


async def scalar(conn, sql):
    return (await conn.fetch_one(sql))[0]


async def main():
    a, b = instance('review_a'), instance('review_b')
    wa, wb = a.db_conn_manager.db_for_write(), b.db_conn_manager.db_for_write()
    failures = []
    results = []

    async def check(name, fn):
        set_current_fastpg('review_a')
        try:
            async with wa.database.transaction(force_rollback=True):
                detail = await fn()
            results.append(name)
            print('PASS:', name, '-', detail)
        except Exception as exc:
            failures.append(name)
            print('FAIL:', name, '-', type(exc).__name__, str(exc))

    try:
        await a.db_conn_manager.connect_all()
        await b.db_conn_manager.connect_all()
        async with wa.database.transaction(force_rollback=True), wb.database.transaction(force_rollback=True):
            await fixtures(wa, 'A')
            await fixtures(wb, 'B')
            print('PostgreSQL:', await scalar(wa, 'SHOW server_version'))

            async def injection():
                try:
                    async with wa.database.transaction(force_rollback=True):
                        await users().filter(id=1).update(id__add="0, name='injected'")
                except (DatabaseError, ValueError, TypeError):
                    pass
                else:
                    raise AssertionError('injected value was accepted')
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=1') == 'A'
                return 'injected arithmetic rejected; row unchanged'

            async def routing():
                obj = await users().get(id=1)
                set_current_fastpg('review_b')
                User.async_queryset
                set_current_fastpg('review_a')
                obj.name = 'wrong_connection'
                await obj.save()
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=1') == 'wrong_connection'
                assert await scalar(wb, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=1') == 'B'
                return 'save used the originating instance A'

            async def dropped_update():
                assert len(await related_users()) == 1
                affected = await related_users().update(name='changed')
                assert affected == 1
                return 'read matched 1 row; UPDATE changed 1 row'

            async def dropped_delete():
                assert len(await related_users()) == 1
                affected = await related_users().delete()
                assert affected == 1
                return 'read matched 1 row; DELETE removed 1 row'

            async def dropped_count():
                assert len(await related_users()) == 1
                assert await related_users().count() == 1
                return 'read matched 1 row; COUNT returned 1'

            async def dropped_lock():
                assert len(await related_users()) == 1
                rows = await related_users().lock_for_update()
                assert len(rows) == 1 and rows[0].profile.bio == 'keep'
                return 'locked query preserved filtering and hydration'

            async def repeated_await():
                qs = users().all()
                records = await qs
                assert await qs is records
                return 'unchanged queryset returned its cached result'

            async def pagination():
                paginator = AsyncPaginator(1, users().all().order_by(id='ASC'))
                assert len((await paginator.get_page(1))['results']) == 1
                assert (await paginator.get_page(2))['results'][0].id == 2
                return 'page 2 fetched the next row'

            async def write_after_read():
                qs = users().filter(id=1)
                records = await qs
                assert await qs.update(name='changed') == 1
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=1') == 'changed'
                return 'UPDATE executed after the read'

            async def relation_save():
                obj = await users().select_related('profile').get(id=1)
                obj.name = 'saved'
                assert await obj.save()
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=1') == 'saved'
                obj.profile.bio = 'saved profile'
                assert await obj.profile.save()
                return 'base and related objects saved without writing hydration attributes'

            async def collision():
                with patch('random.randint', return_value=42):
                    q = Q(id=1) | Q(id=2)
                rows = await users().filter(q)
                assert sorted(row.id for row in rows) == [1, 2]
                return 'same-field OR preserved both values despite patched random source'

            async def joined_prefetch():
                rows = await users().select_related('profile').prefetch_related(
                    Prefetch('posts', Post.async_queryset.using('default').all())
                ).all()
                assert all(len(row.posts) == 1 and row.posts[0].user_id == row.id for row in rows)
                return 'both profiles and posts loaded'

            async def prefetch_count():
                assert await users().prefetch_related(
                    Prefetch('posts', Post.async_queryset.using('default').all())
                ).count() == 2
                return 'count bypassed child hydration'

            async def update_operators():
                assert await users().filter(id=1).update(id__add=10) == 1
                assert await users().filter(id=11).update(id__sub=10) == 1
                assert await users().filter(id=1).update(id__mul=3) == 1
                assert await users().filter(id=3).update(id__div=3) == 1
                assert await users().filter(id=1).update(id__add=3, id__mul=2) == 1
                assert await scalar(wa, 'SELECT id FROM pg_temp.fastpg_review_users WHERE name=\'A\' AND profile_id=10') == 8
                key = "owner's,{tag}"
                qs = Values.async_queryset.using('default')
                assert await qs.filter(id=1).update(**{
                    f'properties__jsonb_set__{key}': "O'Reilly",
                    'properties__jsonb_set__color': 'blue',
                    f'other__jsonb_set__{key}': 'different',
                }) == 1
                row = await qs.get(id=1)
                assert row.properties == {key: "O'Reilly", 'color': 'blue'}
                assert row.other == {key: 'different'}
                assert await qs.update(properties__jsonb_remove=key, expires__add_time='2 hours') == 1
                row = await qs.get(id=1)
                assert row.properties == {'color': 'blue'}
                assert row.expires == datetime(2026, 9, 9, tzinfo=timezone.utc) + timedelta(hours=2)
                assert await qs.update(properties__jsonb_set__discard=True, properties__jsonb={'new': True}, expires__sub_time='2 hours') == 1
                row = await qs.get(id=1)
                assert row.properties == {'new': True}
                assert row.expires == datetime(2026, 9, 9, tzinfo=timezone.utc)
                return 'arithmetic, intervals, JSON paths, removal and replacement work with bound values'

            async def prefetch_reuse():
                prefetch = Prefetch('posts', Post.async_queryset.using('default').filter(id__gt=0))
                qs = users().prefetch_related(prefetch).all().order_by(id='ASC').limit(1)
                first = (await qs)[0]
                assert first.posts[0].id == 100
                assert await first.save()
                second = (await qs.offset(1))[0]
                assert second.posts[0].id == 200
                assert 'user_id' not in prefetch.queryset.where_conditions
                second_dict = (await qs.return_as(ReturnType.DICT))[0]
                assert second_dict['posts'][0]['id'] == 200
                return 'prefetch templates remain reusable across pages and return formats'

            async def null_related_filter():
                await users().create(id=3, name='orphan', profile_id=99)
                qs = users().select_related('profile').filter_related(profile__bio__isnull=True).all()
                assert (await qs)[0].profile is None
                assert await qs.count() == 1
                assert await qs.update(name='changed') == 1
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=3') == 'changed'
                assert await qs.delete() == 1
                assert await scalar(wa, 'SELECT count(*) FROM pg_temp.fastpg_review_users') == 2
                return 'related-only filters retain LEFT JOIN null semantics for reads and writes'

            async def write_cache():
                qs = users().filter(id=1).update(id__add=10)
                assert await qs == 1
                assert await qs == 1
                assert await scalar(wa, 'SELECT count(*) FROM pg_temp.fastpg_review_users WHERE id=11') == 1
                return 'repeated await of an unchanged write does not execute it twice'

            async def input_validation():
                for build in (
                    lambda: users().filter(id=1).update(**{"name = 'injected'": 'bad'}),
                    lambda: users().filter(**{"id); SELECT 1; --": 1}),
                    lambda: users().columns('id, name'),
                    lambda: users().order_by(id='ASC; SELECT 1'),
                    lambda: users().limit('1; SELECT 1'),
                    lambda: users().offset(-1),
                ):
                    try:
                        build()
                    except ValueError:
                        pass
                    else:
                        raise AssertionError('invalid query input was accepted')
                assert await users().all().limit(0) == []
                return 'invalid identifiers, sort directions and pagination rejected; limit(0) returns no rows'

            async def insert_payloads():
                obj = await users().create(id=3, name='created', profile_id=10, extra_payload='ignored')
                set_current_fastpg('review_b')
                User.async_queryset
                obj.name = 'saved to A'
                assert await obj.save()
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=3') == 'saved to A'
                set_current_fastpg('review_a')
                await users().bulk_create(
                    [{'id': 3, 'name': 'upserted', 'profile_id': 10, 'extra_payload': 'ignored'}],
                    on_conflict=OnConflict.UPDATE, conflict_target=['id'], update_fields=['name'],
                )
                assert await scalar(wa, 'SELECT name FROM pg_temp.fastpg_review_users WHERE id=3') == 'upserted'
                try:
                    await users().bulk_create([{'id': 4, 'name': 'bad', 'profile_id': 10}],
                                              on_conflict=OnConflict.UPDATE, conflict_target=['id); SELECT 1'], update_fields=['name'])
                except ValueError:
                    pass
                else:
                    raise AssertionError('invalid conflict field was accepted')
                assert await obj.delete()
                return 'create and upsert write declared fields; created objects retain their connection'

            for name, fn in (
                ('SQL injection', injection),
                ('shared write connection', routing),
                ('related predicate UPDATE', dropped_update),
                ('related predicate DELETE', dropped_delete),
                ('related predicate COUNT', dropped_count),
                ('related predicate FOR UPDATE', dropped_lock),
                ('repeated await', repeated_await),
                ('paginator second page', pagination),
                ('write after read', write_after_read),
                ('save with loaded relation', relation_save),
                ('Q parameter collision', collision),
                ('combined join and prefetch', joined_prefetch),
                ('prefetch count', prefetch_count),
                ('legitimate update operators', update_operators),
                ('prefetch reuse and save', prefetch_reuse),
                ('related-only NULL predicates', null_related_filter),
                ('write cache', write_cache),
                ('query input validation', input_validation),
                ('insert payloads and connection binding', insert_payloads),
            ):
                await check(name, fn)
        print('RESULT:', len(results), 'passed;', len(failures), 'failed; outer transactions rolled back')
        assert not failures, failures
    finally:
        await a.db_conn_manager.close_all()
        await b.db_conn_manager.close_all()


if __name__ == '__main__':
    asyncio.run(main())
