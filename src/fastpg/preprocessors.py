from datetime import datetime
import pytz

IST_TZ = pytz.timezone("Asia/Kolkata")


class PreCreateProcessors:

    @staticmethod
    def model_obj_populate_auto_now_add_fields(model_obj):
        try:
            for field_name in model_obj.Meta.auto_now_add_fields:
                setattr(model_obj, field_name, datetime.now(IST_TZ))
        except AttributeError:
            pass

    @staticmethod
    def model_dict_populate_auto_generated_fields(model_dict, model_cls):
        try:
            for field_name in model_cls.Meta.auto_generated_fields:
                del model_dict[field_name]
        except AttributeError:
            pass


class PreSaveProcessors:

    @staticmethod
    def model_obj_populate_auto_now_fields(model_obj):
        try:
            for field_name in model_obj.Meta.auto_now_fields:
                setattr(model_obj, field_name, datetime.now(IST_TZ))
        except AttributeError:
            pass
