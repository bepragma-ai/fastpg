import pytest
from pydantic import BaseModel

from fastpg.errors import InvalidINClauseValueError, MalformedMetaError, UnsupportedOperatorError
from fastpg.utils import Q, Relation


class User(BaseModel):
    id: int
    name: str

    class Meta:
        db_table = "users"
        primary_key = "id"


class MissingMetaModel(BaseModel):
    id: int


class UserProfile(BaseModel):
    id: int
    user_id: int

    class Meta:
        db_table = "user_profiles"
        primary_key = "id"


def test_relation_default_related_name_and_on_clause():
    relation = Relation(UserProfile, foreign_field="user_id")

    assert relation.related_name == "user_profile"
    assert relation.render_on_clause() == "t.user_id = r.id"


def test_relation_missing_meta_raises():
    with pytest.raises(MalformedMetaError):
        Relation(MissingMetaModel, foreign_field="user_id")


def test_q_equality_clause_is_deterministic(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 42)
    query = Q(name="Alice")

    assert query.where_clause == "t.name = :t_name_1_42"
    assert query.params == {"t_name_1_42": "Alice"}


def test_q_in_clause_builds_params(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 7)
    query = Q(id__in=[1, 2])

    assert query.where_clause == "t.id IN (:t_id_1_7_0,:t_id_1_7_1)"
    assert query.params == {"t_id_1_7_0": 1, "t_id_1_7_1": 2}


def test_q_isnull_clause(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 9)

    assert Q(deleted_at__isnull=True).where_clause == "t.deleted_at IS NULL"
    assert Q(deleted_at__isnull=False).where_clause == "t.deleted_at IS NOT NULL"


def test_q_contains_clause(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 3)
    query = Q(name__contains="bob")

    assert query.where_clause == "t.name LIKE :t_name_1_3"
    assert query.params == {"t_name_1_3": "%bob%"}


def test_q_invalid_operator_raises():
    with pytest.raises(UnsupportedOperatorError):
        Q(name__nope="bob")


def test_q_invalid_in_clause_raises():
    with pytest.raises(InvalidINClauseValueError):
        Q(id__in="nope")

    with pytest.raises(InvalidINClauseValueError):
        Q(id__in=[])
