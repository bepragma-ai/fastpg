"""Utility preprocessors for automatic field handling."""

from datetime import datetime
import os
import pytz


def _get_timezone():
    """Return the configured timezone.

    The timezone name is read from the ``FASTPG_TZ`` environment variable. If the
    variable is not set or invalid, UTC is used.
    """

    tz_name = os.getenv("FASTPG_TZ", "UTC")
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        return pytz.UTC


class PreCreateProcessors:
    """Pre-save hooks applied before creating a model instance."""

    @staticmethod
    def model_obj_populate_auto_now_add_fields(model_obj):
        """Populate ``auto_now_add`` fields on the given model instance."""
        try:
            for field_name in model_obj.Meta.auto_now_add_fields:
                setattr(model_obj, field_name, datetime.now(_get_timezone()))
        except AttributeError:
            pass

    @staticmethod
    def model_dict_populate_auto_generated_fields(model_dict, model_cls):
        """Remove auto-generated fields from the model dictionary before insert."""
        try:
            for field_name in model_cls.Meta.auto_generated_fields:
                del model_dict[field_name]
        except AttributeError:
            pass


class PreSaveProcessors:
    """Pre-save hooks applied before updating a model instance."""

    @staticmethod
    def model_obj_populate_auto_now_fields(model_obj):
        """Populate ``auto_now`` fields on the given model instance."""
        try:
            for field_name in model_obj.Meta.auto_now_fields:
                setattr(model_obj, field_name, datetime.now(_get_timezone()))
        except AttributeError:
            pass
