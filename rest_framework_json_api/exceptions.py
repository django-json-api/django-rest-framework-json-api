from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status
import re
from rest_framework.response import Response
from django.core.exceptions import FieldDoesNotExist, FieldError
from rest_framework_json_api import utils

def rendered_with_json_api(view):
    from rest_framework_json_api.renderers import JSONRenderer
    for renderer_class in getattr(view, 'renderer_classes', []):
        if issubclass(renderer_class, JSONRenderer):
            return True
    return False

def unhandled_drf_exception_handler(exc, context):
    """
    Deals with exceptions that DRF doesn't catch, specifically for filter & sort query parameters:
    "Cannot resolve keyword 'xname' into field. Choices are: name, title, ...."

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
                "status": 500,
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
    is_uniform = getattr(settings, 'JSON_API_UNIFORM_EXCEPTIONS', False)
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
