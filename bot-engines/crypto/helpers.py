import json
import sys
from datetime import datetime, date
from crypto.structs import Market, Balance, Order


def print_json(data):
    print(json.dumps(data, indent=2))


def str_to_class(str):
    return getattr(sys.modules["crypto"], str)


def serialize_obj(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Market):
        return obj.counter.upper() + "_" + obj.base.upper()
    elif isinstance(obj, (Balance, Order)):
        return obj.__dict__
    elif isinstance(obj, (json.JSONDecodeError, Exception)):
        return str(obj)


