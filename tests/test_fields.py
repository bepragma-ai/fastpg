import json
from datetime import datetime

from fastpg.fields import CustomJsonEncoder, json_str_to_dict, serialize_json_data, validate_json_data


def test_json_str_to_dict():
    assert json_str_to_dict('{"a": 1}') == {"a": 1}
    assert json_str_to_dict({"a": 1}) == {"a": 1}


def test_validate_json_data():
    data = {"a": 1}
    rendered = validate_json_data(data)
    assert json.loads(rendered) == data


def test_serialize_json_data_respects_context():
    data = {"a": 1}
    result = serialize_json_data(data, info=type("Info", (), {"context": {"db_write": True}})())
    assert json.loads(result) == data

    result_no_context = serialize_json_data(data, info=type("Info", (), {"context": {}})())
    assert result_no_context == data


def test_custom_json_encoder_handles_datetime():
    when = datetime(2023, 1, 1, 12, 0, 0)
    encoded = json.dumps({"when": when}, cls=CustomJsonEncoder)
    assert "2023-01-01T12:00:00" in encoded
