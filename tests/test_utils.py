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


def test_q_builds_where_clause_with_ops():
    q = Q(name__contains="bob", age__gte=18, active__isnull=False)
    assert f"t.name LIKE :t_name_1_{q.secret}" in q.where_clause
    assert f"t.age >= :t_age_2_{q.secret}" in q.where_clause
    assert "t.active IS NOT NULL" in q.where_clause
    assert q.params[f"t_name_1_{q.secret}"] == "%bob%"
    assert q.params[f"t_age_2_{q.secret}"] == 18


def test_q_in_clause_requires_list():
    with pytest.raises(InvalidINClauseValueError):
        Q(id__in="not-a-list")
    with pytest.raises(InvalidINClauseValueError):
        Q(id__in=[])


def test_q_invalid_operator_raises():
    with pytest.raises(UnsupportedOperatorError):
        Q(name__bogus="nope")


def test_q_and_or_merge():
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


def test_relation_resolves_model_defined_later():
    class Employee(DatabaseModel):
        location_id: int

        class Meta:
            db_table = "employees"
            primary_key = "location_id"
            relations = {
                "location": Relation(
                    "test_utils.LocationDefinedLater",
                    foreign_field="location_id",
                )
            }

    class LocationDefinedLater(DatabaseModel):
        id: int

        class Meta:
            db_table = "locations"
            primary_key = "id"

    relation = Employee.Meta.relations["location"]
    assert relation.RelatedModel is LocationDefinedLater
    assert relation.table == "locations"
