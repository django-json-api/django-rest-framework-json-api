"""
Utils.
"""
import inflection

from django.core import urlresolvers
from django.conf import settings
from django.utils import six, encoding
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.utils.translation import ugettext_lazy as _

from rest_framework.serializers import BaseSerializer
from rest_framework.relations import RelatedField, HyperlinkedRelatedField
from rest_framework.settings import api_settings
from rest_framework.exceptions import APIException

try:
    from rest_framework.compat import OrderedDict
except ImportError:
    OrderedDict = dict

try:
    from rest_framework.serializers import ManyRelatedField
except ImportError:
    ManyRelatedField = type(None)


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

    try:
        resource_name = getattr(view, 'resource_name')
    except AttributeError:
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

            # if the name was calculated automatically then pluralize and format
            if not isinstance(resource_name, six.string_types):
                return resource_name

            resource_name = inflection.pluralize(resource_name.lower())

            format_type = getattr(settings, 'JSON_API_FORMAT_KEYS', False)
            if format_type == 'dasherize':
                resource_name = inflection.dasherize(resource_name)
            elif format_type == 'camelize':
                resource_name = inflection.camelize(resource_name)
            elif format_type == 'underscore':
                resource_name = inflection.underscore(resource_name)

    return resource_name


def format_keys(obj, format_type=None):
    """
    Takes either a dict or list and returns it with camelized keys only if
    JSON_API_FORMAT_KEYS is set.

    :format_type: Either 'dasherize', 'camelize' or 'underscore'
    """
    if format_type is None:
        format_type = getattr(settings, 'JSON_API_FORMAT_KEYS', False)

    if format_type in ('dasherize', 'camelize', 'underscore'):

        if isinstance(obj, dict):
            formatted = OrderedDict()
            for key, value in obj.items():
                if format_type == 'dasherize':
                    formatted[inflection.dasherize(key)] \
                        = format_keys(value, format_type)
                elif format_type == 'camelize':
                    formatted[inflection.camelize(key, False)] \
                        = format_keys(value, format_type)
                elif format_type == 'underscore':
                    formatted[inflection.underscore(key)] \
                        = format_keys(value, format_type)
            return formatted
        if isinstance(obj, list):
            return [format_keys(item, format_type) for item in obj]
        else:
            return obj
    else:
        return obj


def extract_id_from_url(url):
    http_prefix = url.startswith(('http:', 'https:'))
    if http_prefix:
        # If needed convert absolute URLs to relative path
        data = urlparse(url).path
        prefix = urlresolvers.get_script_prefix()
        if data.startswith(prefix):
            url = '/' + data[len(prefix):]

    match = urlresolvers.resolve(url)
    return encoding.force_text(match.kwargs['pk'])


def extract_id(fields, resource):
    for field_name, field in six.iteritems(fields):
        if field_name == 'id':
            return encoding.force_text(resource[field_name])
        if field_name == api_settings.URL_FIELD_NAME:
            return extract_id_from_url(resource[field_name])


def extract_attributes(fields, resource):
    data = OrderedDict()
    for field_name, field in six.iteritems(fields):
        # ID is always provided in the root of JSON API so remove it from attrs
        if field_name == 'id':
            continue
        # Skip fields with relations
        if isinstance(field, (RelatedField, BaseSerializer, ManyRelatedField)):
            continue

        data.update({field_name: encoding.force_text(resource[field_name])})

    return format_keys(data)


def extract_relationships(fields, resource):
    data = OrderedDict()
    for field_name, field in six.iteritems(fields):
        # Skip URL field
        if field_name == api_settings.URL_FIELD_NAME:
            continue

        # Skip fields without relations
        if not isinstance(field, (RelatedField, BaseSerializer, ManyRelatedField)):
            continue

        if isinstance(field, ManyRelatedField):
            relation_data = list()

            relation = field.child_relation
            model = relation.queryset.model
            relation_type = inflection.pluralize(model.__name__).lower()

            if isinstance(relation, HyperlinkedRelatedField):
                for link in resource[field_name]:
                    relation_data.append(OrderedDict([('type', relation_type), ('id', extract_id_from_url(link))]))

                data.update({field_name: {'data': relation_data}})

    return format_keys(data)
