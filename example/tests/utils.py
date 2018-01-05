import json

from django.utils.encoding import force_text


def load_json(data):
    return json.loads(force_text(data))
