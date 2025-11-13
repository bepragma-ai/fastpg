import json
from uuid import uuid4
from datetime import datetime
from typing import Any, Annotated, Dict

from pydantic import (
    Json,
    SerializationInfo,
    BeforeValidator,
    PlainSerializer,
)


def json_str_to_dict(value:Any) -> Dict:
    """
    Converts JSON string (typically read from DB) to dictionary
    """
    if isinstance(value, str):
        return json.loads(value)
    return value


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def validate_json_data(data:Any) -> str|Dict:
    if isinstance(data, (dict, list)):
        return json.dumps(data, cls=CustomJsonEncoder)
    return data

def serialize_json_data(data, info:SerializationInfo) -> str|Dict:
    if info.context and info.context.get('db_write'):
        return json.dumps(data, cls=CustomJsonEncoder)
    return data

JsonData = Annotated[
    Json,
    BeforeValidator(validate_json_data),
    PlainSerializer(serialize_json_data, return_type=str|Dict),
]
