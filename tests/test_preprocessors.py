from datetime import datetime

import pytz

from fastpg.fastpg import FAST_PG
from fastpg.preprocessors import PreCreateProcessors, PreSaveProcessors


class DummyModel:
    class Meta:
        auto_now_add_fields = ["created_at"]
        auto_now_fields = ["updated_at"]
        auto_generated_fields = ["id"]

    def __init__(self):
        self.created_at = None
        self.updated_at = None


def test_precreate_populates_auto_now_add_fields(monkeypatch):
    monkeypatch.setattr(FAST_PG, "TZ", pytz.UTC)
    model = DummyModel()

    PreCreateProcessors.model_obj_populate_auto_now_add_fields(model)

    assert isinstance(model.created_at, datetime)
    assert model.created_at.tzinfo == pytz.UTC


def test_presave_populates_auto_now_fields(monkeypatch):
    monkeypatch.setattr(FAST_PG, "TZ", pytz.UTC)
    model = DummyModel()

    PreSaveProcessors.model_obj_populate_auto_now_fields(model)

    assert isinstance(model.updated_at, datetime)
    assert model.updated_at.tzinfo == pytz.UTC


def test_precreate_removes_auto_generated_fields():
    model_dict = {"id": 1, "name": "test"}

    PreCreateProcessors.model_dict_populate_auto_generated_fields(model_dict, DummyModel)

    assert model_dict == {"name": "test"}
