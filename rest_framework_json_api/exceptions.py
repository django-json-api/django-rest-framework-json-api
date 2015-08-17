from django.utils import encoding
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from rest_framework_json_api.utils import format_value


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    errors = []
    # handle generic errors. ValidationError('test') in a view for example
    if isinstance(response.data, list):
        for message in response.data:
            errors.append({
                'detail': message,
                'source': {
                    'pointer': '/data',
                },
                'status': encoding.force_text(response.status_code),
            })
    # handle all errors thrown from serializers
    else:
        for field, error in response.data.items():
            field = format_value(field)
            pointer = '/data/attributes/{}'.format(field)
            # see if they passed a dictionary to ValidationError manually
            if isinstance(error, dict):
                errors.append(error)
            else:
                for message in error:
                    errors.append({
                        'detail': message,
                        'source': {
                            'pointer': pointer,
                        },
                        'status': encoding.force_text(response.status_code),
                    })

    context['view'].resource_name = 'errors'
    response.data = errors
    return response


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict.')
