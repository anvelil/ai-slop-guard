import json


def to_json(payload):
    return json.dumps(payload)


_ = to_json({"a": 1})
