import pytest

from fastpg.utils import Q, Relation
from fastpg.errors import InvalidINClauseValueError, UnsupportedOperatorError
from fastpg.core import DatabaseModel


class UserProfile(DatabaseModel):
    id: int

    class Meta:
        db_table = "user_profiles"
        primary_key = "id"


def test_relation_default_related_name():
    relation = Relation(UserProfile, foreign_field="profile_id")
    assert relation.related_name == "user_profile"
    assert relation.render_on_clause() == "t.profile_id = r.id"


def test_q_builds_where_clause_with_ops(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 123)
    q = Q(name__contains="bob", age__gte=18, active__isnull=False)
    assert "t.name LIKE :t_name_1_123" in q.where_clause
    assert "t.age >= :t_age_2_123" in q.where_clause
    assert "t.active IS NOT NULL" in q.where_clause
    assert q.params["t_name_1_123"] == "%bob%"
    assert q.params["t_age_2_123"] == 18


def test_q_in_clause_requires_list(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 1)
    with pytest.raises(InvalidINClauseValueError):
        Q(id__in="not-a-list")
    with pytest.raises(InvalidINClauseValueError):
        Q(id__in=[])


def test_q_invalid_operator_raises():
    with pytest.raises(UnsupportedOperatorError):
        Q(name__bogus="nope")


def test_q_and_or_merge(monkeypatch):
    monkeypatch.setattr("fastpg.utils.random.randint", lambda *_: 5)
    q1 = Q(name="alice")
    q2 = Q(age__gt=30)
    combined_or = q1 | q2
    combined_and = q1 & q2
    assert " OR " in combined_or.where_clause
    assert " AND " in combined_and.where_clause
    assert set(combined_or.params.keys()) == set(q1.params.keys()) | set(q2.params.keys())


def test_relation_raises_for_missing_meta():
    class BadModel:
        pass

    with pytest.raises(AttributeError):
        Relation(BadModel, foreign_field="profile_id")
