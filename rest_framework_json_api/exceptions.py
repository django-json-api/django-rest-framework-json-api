from django.utils.translation import ugettext_lazy as _
from rest_framework import status, exceptions

from rest_framework_json_api import utils


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
    return utils.format_drf_errors(response, context, exc)


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict.')
