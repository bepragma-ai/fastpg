from datetime import datetime
from typing import Optional

from fastpg.constants import ConnectionType
from fastpg.fastpg import create_fastpg
from fastpg.core import DatabaseModel
from fastpg.preprocessors import PreCreateProcessors, PreSaveProcessors


class AuditModel(DatabaseModel):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Meta:
        db_table = "audit_models"
        primary_key = "id"
        auto_now_add_fields = ["created_at"]
        auto_now_fields = ["updated_at"]


def _config():
    return {
        "read": {
            "TYPE": ConnectionType.READ,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
        "write": {
            "TYPE": ConnectionType.WRITE,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
    }


def test_precreate_populates_auto_now_add():
    create_fastpg(databases=_config(), fastpg_tz="UTC")
    obj = AuditModel(id=1)
    PreCreateProcessors.model_obj_populate_auto_now_add_fields(obj)
    assert obj.created_at is not None


def test_presave_populates_auto_now():
    create_fastpg(databases=_config(), fastpg_tz="UTC")
    obj = AuditModel(id=1)
    PreSaveProcessors.model_obj_populate_auto_now_fields(obj)
    assert obj.updated_at is not None
