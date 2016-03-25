import inspect
from django.utils import six, encoding
from django.utils.translation import ugettext_lazy as _
from rest_framework import status, exceptions

from rest_framework_json_api.utils import format_value


def exception_handler(exc, context):
    # Import this here to avoid potential edge-case circular imports, which
    # crashes with:
    # "ImportError: Could not import 'rest_framework_json_api.parsers.JSONParser' for API setting
    # 'DEFAULT_PARSER_CLASSES'. ImportError: cannot import name 'exceptions'.'"
    #
    # Also see: https://github.com/django-json-api/django-rest-framework-json-api/issues/158
    from rest_framework.views import exception_handler as drf_exception_handler
    response = drf_exception_handler(exc, context)

    if not response:
        return response

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
            elif isinstance(error, six.string_types):
                classes = inspect.getmembers(exceptions, inspect.isclass)
                # DRF sets the `field` to 'detail' for its own exceptions
                if isinstance(exc, tuple(x[1] for x in classes)):
                    pointer = '/data'
                errors.append({
                    'detail': error,
                    'source': {
                        'pointer': pointer,
                    },
                    'status': encoding.force_text(response.status_code),
                })
            elif isinstance(error, list):
                for message in error:
                    errors.append({
                        'detail': message,
                        'source': {
                            'pointer': pointer,
                        },
                        'status': encoding.force_text(response.status_code),
                    })
            else:
                errors.append({
                    'detail': error,
                    'source': {
                        'pointer': pointer,
                    },
                    'status': encoding.force_text(response.status_code),
                })


    context['view'].resource_name = 'errors'
    response.data = errors
    return response


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict.')

