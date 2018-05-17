import re

from django.core.exceptions import FieldDoesNotExist, FieldError
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.response import Response

from rest_framework_json_api import utils

from .settings import json_api_settings


def rendered_with_json_api(view):
    from rest_framework_json_api.renderers import JSONRenderer
    for renderer_class in getattr(view, 'renderer_classes', []):
        if issubclass(renderer_class, JSONRenderer):
            return True
    return False


def unhandled_drf_exception_handler(exc, context):
    """
    Deal with exceptions that DRF doesn't catch and return a JSON:API errors object.

    For model query parameters, attempt to identify the parameter that caused the exception:
    "Cannot resolve keyword 'xname' into field. Choices are: name, title, ...."
    Unfortunately there's no "clean" way to identify which field caused the exception other than
    parsing the error message. If the parse fails, a more generic error is reported.

    Even a 500 error for a jsonapi view should return a jsonapi error object, not an HTML response.
    """
    if not rendered_with_json_api(context['view']):
        return None
    keymatch = re.compile(r"^Cannot resolve keyword '(?P<keyword>\w+)' into field.")
    if isinstance(exc, (FieldError, FieldDoesNotExist,)):
        matched = keymatch.match(str(exc))
        bad_kw = matched.group("keyword") if matched else "?"
        status_code = 400
        errors = [
            {
                "status": status_code,
                "code": "field_error",
                "title": "Field error",
                "detail": str(exc),
                "source": {
                    "pointer": context["request"].path,
                    "parameter": bad_kw
                }
            }
        ]
    else:
        status_code = 500
        errors = [
            {
                "status": status_code,
                "code": "server_error",
                "title": "Internal Server Error",
                "detail": str(exc),
                "source": {
                    "pointer": context["request"].path,
                }
            }
        ]
    return Response(errors, status=status_code)


def exception_handler(exc, context):
    # Import this here to avoid potential edge-case circular imports, which
    # crashes with:
    # "ImportError: Could not import 'rest_framework_json_api.parsers.JSONParser' for API setting
    # 'DEFAULT_PARSER_CLASSES'. ImportError: cannot import name 'exceptions'.'"
    #
    # Also see: https://github.com/django-json-api/django-rest-framework-json-api/issues/158
    from rest_framework.views import exception_handler as drf_exception_handler

    # Render exception with DRF
    response = drf_exception_handler(exc, context)
    if not response:
        return unhandled_drf_exception_handler(exc, context)

    # Use regular DRF format if not rendered by DRF JSON API and not uniform
    is_json_api_view = rendered_with_json_api(context['view'])
    is_uniform = json_api_settings.UNIFORM_EXCEPTIONS
    if not is_json_api_view and not is_uniform:
        return response

    # Convert to DRF JSON API error format
    response = utils.format_drf_errors(response, context, exc)

    # Add top-level 'errors' object when not rendered by DRF JSON API
    if not is_json_api_view:
        response.data = utils.format_errors(response.data)

    return response


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict.')
