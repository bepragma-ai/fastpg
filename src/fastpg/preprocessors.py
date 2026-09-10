"""Utility preprocessors for automatic field handling."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import DatabaseModel

from .fastpg import get_fastpg


class PreCreateProcessors:
    """Pre-save hooks applied before creating a model instance."""

    @staticmethod
    def model_obj_populate_auto_now_add_fields(model_obj: DatabaseModel) -> None:
        """Populate ``auto_now_add`` fields on the given model instance."""
        try:
            fastpg = get_fastpg()
            for field_name in model_obj.Meta.auto_now_add_fields:
                if getattr(model_obj, field_name) is None:
                    setattr(model_obj, field_name, datetime.now(fastpg.TZ))
        except AttributeError:
            pass

    @staticmethod
    def model_dict_populate_auto_generated_fields(model_dict: Dict[str, Any], model_cls: Type[DatabaseModel]) -> None:
        """Remove auto-generated fields from the model dictionary before insert."""
        try:
            for field_name in model_cls.Meta.auto_generated_fields:
                del model_dict[field_name]
        except AttributeError:
            pass


class PreSaveProcessors:
    """Pre-save hooks applied before updating a model instance."""

    @staticmethod
    def model_obj_populate_auto_now_fields(model_obj: DatabaseModel) -> None:
        """Populate ``auto_now`` fields on the given model instance."""
        try:
            fastpg = get_fastpg()
            for field_name in model_obj.Meta.auto_now_fields:
                if getattr(model_obj, field_name) is None:
                    setattr(model_obj, field_name, datetime.now(fastpg.TZ))
        except AttributeError:
            pass
