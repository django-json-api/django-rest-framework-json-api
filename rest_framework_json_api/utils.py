"""
Utils.
"""
import inflection

from rest_framework.exceptions import APIException

from django.conf import settings
from django.utils import six
from django.utils.translation import ugettext_lazy as _

try:
    from rest_framework.compat import OrderedDict
except ImportError:
    OrderedDict = dict


def get_resource_name(context):
    """
    Return the name of a resource.
    """
    view = context.get('view')

    # Sanity check to make sure we have a view.
    if not view:
        raise APIException(_('Could not find view.'))

    # Check to see if there is a status code and return early
    # with the resource_name value of `errors`.
    try:
        code = str(view.response.status_code)
    except (AttributeError, ValueError):
        pass
    else:
        if code.startswith('4') or code.startswith('5'):
            return 'errors'

    resource_name = getattr(view, 'resource_name')
    if not resource_name:
        try:
            # Check the meta class
            resource_name = (
                getattr(view, 'serializer_class')
                .Meta.resource_name)
        except AttributeError:
            # Use the model
            try:
                resource_name = (
                    getattr(view, 'serializer_class')
                    .Meta.model.__name__)
            except AttributeError:
                try:
                    resource_name = view.model.__name__
                except AttributeError:
                    resource_name = view.__class__.__name__

    if isinstance(resource_name, six.string_types):
        return inflection.camelize(resource_name, False)

    return resource_name


def format_keys(obj, format_type=None):
    """
    Takes either a dict or list and returns it with camelized keys only if
    REST_EMBER_FORMAT_KEYS is set.

    :format_type: Either 'camelize' or 'underscore'
    """
    if (getattr(settings, 'REST_EMBER_FORMAT_KEYS', False)
            and format_type in ('camelize', 'underscore')):

        if isinstance(obj, dict):
            formatted = OrderedDict()
            for key, value in obj.items():
                if format_type == 'camelize':
                    formatted[inflection.camelize(key, False)]\
                        = format_keys(value, format_type)
                elif format_type == 'underscore':
                    formatted[inflection.underscore(key)]\
                        = format_keys(value, format_type)
            return formatted
        if isinstance(obj, list):
            return [format_keys(item, format_type) for item in obj]
        else:
            return obj
    else:
        return obj


def format_resource_name(obj, name):
    """
    Pluralize the resource name if more than one object in results.
    """
    if (getattr(settings, 'REST_EMBER_PLURALIZE_KEYS')
            and isinstance(obj, list)):

        return inflection.pluralize(name)
    return name
