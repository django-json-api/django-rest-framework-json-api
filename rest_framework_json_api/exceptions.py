from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status

from rest_framework_json_api import utils

from .settings import json_api_settings


def rendered_with_json_api(view):
    from rest_framework_json_api.renderers import JSONRenderer
    for renderer_class in getattr(view, 'renderer_classes', []):
        if issubclass(renderer_class, JSONRenderer):
            return True
    return False


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
        return response

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
