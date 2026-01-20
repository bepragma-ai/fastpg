import json

from pydantic import BaseModel

from fastpg.fields import JsonData, json_str_to_dict, validate_json_data


class Payload(BaseModel):
    payload: JsonData


def test_json_str_to_dict_parses_string():
    data = json_str_to_dict('{"a": 1}')
    assert data == {"a": 1}


def test_json_str_to_dict_passthrough():
    value = {"a": 1}
    assert json_str_to_dict(value) is value


def test_validate_json_data_serializes_dict_and_list():
    assert json.loads(validate_json_data({"a": 1})) == {"a": 1}
    assert json.loads(validate_json_data([1, 2])) == [1, 2]


def test_jsondata_serialization_context():
    instance = Payload(payload={"key": "value"})

    assert instance.model_dump() == {"payload": {"key": "value"}}
    assert instance.model_dump(context={"db_write": True}) == {"payload": '{"key": "value"}'}
