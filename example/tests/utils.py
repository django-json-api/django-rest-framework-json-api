import json

from django.utils.encoding import force_bytes, force_text


def load_json(data):
    return json.loads(force_text(data))


def dump_json(data):
    '''
    Converts a Python object to a JSON formatted string.
    '''

    json_kwargs = {
        'sort_keys': True,
        'indent': 4,
        'separators': (', ', ': ')
    }

    return force_bytes(json.dumps(data, **json_kwargs))
