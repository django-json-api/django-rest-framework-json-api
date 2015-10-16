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


def redump_json(data):
    '''
    The response.content is already a JSON formatted string BUT
    we don't know anything about its formatting, in particular,
    the indent and separators arguments. DRF has a complex method to
    determine what values to use for each argument and unfortunately,
    the methods aren't the same in all DRF versions.

    So what to do? LOAD the JSON formmated string (response.content)
    as a Python object and DUMP it again and hence the name of this function.

    This will guarantee that we're comparing two similarly formatted JSON
    strings. Only the formatting similarity is guaranteed. As for the content,
    that's what the tests are for!
    '''

    data = json.loads(force_text(data))

    return dump_json(data)
