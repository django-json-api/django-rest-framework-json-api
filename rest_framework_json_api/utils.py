"""
Utils.
"""
import copy
from collections import OrderedDict

import inflection
from django.conf import settings
from django.utils import six
from django.utils.module_loading import import_string as import_class_from_dotted_path
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException

try:
    from rest_framework.serializers import ManyRelatedField
except ImportError:
    ManyRelatedField = type(None)

try:
    from rest_framework_nested.relations import HyperlinkedRouterField
except ImportError:
    HyperlinkedRouterField = type(None)


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
            serializer = view.get_serializer_class()
            resource_name = get_resource_name_from_serializer_or_model(serializer, view)
        except AttributeError:
            resource_name = get_resource_name_from_model_or_relationship(view)

    return resource_name


def get_resource_name_from_serializer_or_model(serializer, view):
    try:
        return get_resource_type_from_serializer(serializer)
    except AttributeError:
        resource_name = get_resource_name_from_model_or_relationship(view)

    return resource_name


def get_resource_name_from_model_or_relationship(view):
    try:
        resource_name = get_resource_type_from_model(view.model)
    except AttributeError:
        resource_name = view.__class__.__name__

    if not isinstance(resource_name, six.string_types):
        # The resource name is not a string - return as is
        return resource_name

    # the name was calculated automatically from the view > pluralize and format
    resource_name = format_relation_name(resource_name)
    return resource_name


def get_serializer_fields(serializer):
    fields = None
    if hasattr(serializer, 'child'):
        fields = getattr(serializer.child, 'fields')
        meta = getattr(serializer.child, 'Meta', None)
    if hasattr(serializer, 'fields'):
        fields = getattr(serializer, 'fields')
        meta = getattr(serializer, 'Meta', None)

    if fields:
        meta_fields = getattr(meta, 'meta_fields', {})
        for field in meta_fields:
            try:
                fields.pop(field)
            except KeyError:
                pass
        return fields

def format_keys(obj, format_type=None):
    """
    Takes either a dict or list and returns it with camelized keys only if
    JSON_API_FORMAT_KEYS is set.

    :format_type: Either 'dasherize', 'camelize' or 'underscore'
    """
    if format_type is None:
        format_type = getattr(settings, 'JSON_API_FORMAT_KEYS', False)

    if format_type in ('dasherize', 'camelize', 'underscore', 'capitalize'):

        if isinstance(obj, dict):
            formatted = OrderedDict()
            for key, value in obj.items():
                if format_type == 'dasherize':
                    # inflection can't dasherize camelCase
                    key = inflection.underscore(key)
                    formatted[inflection.dasherize(key)] \
                        = format_keys(value, format_type)
                elif format_type == 'camelize':
                    formatted[inflection.camelize(key, False)] \
                        = format_keys(value, format_type)
                elif format_type == 'capitalize':
                    formatted[inflection.camelize(key)] \
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


def format_value(value, format_type=None):
    if format_type is None:
        format_type = getattr(settings, 'JSON_API_FORMAT_KEYS', False)
    if format_type == 'dasherize':
        # inflection can't dasherize camelCase
        value = inflection.underscore(value)
        value = inflection.dasherize(value)
    elif format_type == 'camelize':
        value = inflection.camelize(value, False)
    elif format_type == 'capitalize':
        value = inflection.camelize(value)
    elif format_type == 'underscore':
        value = inflection.underscore(value)
    return value


def format_relation_name(value, format_type=None):
    if format_type is None:
        format_type = getattr(settings, 'JSON_API_FORMAT_RELATION_KEYS', False)

    pluralize = getattr(settings, 'JSON_API_PLURALIZE_RELATION_TYPE', False)

    if format_type:
        # format_type will never be None here so we can use format_value
        value = format_value(value, format_type)

    return inflection.pluralize(value) if pluralize else value


def get_related_resource_type(relation):
    if hasattr(relation, '_meta'):
        relation_model = relation._meta.model
    elif hasattr(relation, 'model'):
        # the model type was explicitly passed as a kwarg to ResourceRelatedField
        relation_model = relation.model
    elif hasattr(relation, 'get_queryset') and relation.get_queryset() is not None:
        relation_model = relation.get_queryset().model
    else:
        parent_serializer = relation.parent
        if hasattr(parent_serializer, 'Meta'):
            parent_model = parent_serializer.Meta.model
        else:
            parent_model = parent_serializer.parent.Meta.model

        if relation.source:
            if relation.source != '*':
                parent_model_relation = getattr(parent_model, relation.source)
            else:
                parent_model_relation = getattr(parent_model, relation.field_name)
        else:
            parent_model_relation = getattr(parent_model, parent_serializer.field_name)

        if hasattr(parent_model_relation, 'related'):
            try:
                relation_model = parent_model_relation.related.related_model
            except AttributeError:
                # Django 1.7
                relation_model = parent_model_relation.related.model
        elif hasattr(parent_model_relation, 'field'):
            relation_model = parent_model_relation.field.related.model
        else:
            return get_related_resource_type(parent_model_relation)
    return get_resource_type_from_model(relation_model)


def get_instance_or_manager_resource_type(resource_instance_or_manager):
    if hasattr(resource_instance_or_manager, 'model'):
        return get_resource_type_from_manager(resource_instance_or_manager)
    if hasattr(resource_instance_or_manager, '_meta'):
        return get_resource_type_from_instance(resource_instance_or_manager)
    pass


def get_resource_type_from_model(model):
    json_api_meta = getattr(model, 'JSONAPIMeta', None)
    return getattr(
        json_api_meta,
        'resource_name',
        format_relation_name(model.__name__))


def get_resource_type_from_queryset(qs):
    return get_resource_type_from_model(qs.model)


def get_resource_type_from_instance(instance):
    return get_resource_type_from_model(instance._meta.model)


def get_resource_type_from_manager(manager):
    return get_resource_type_from_model(manager.model)


def get_resource_type_from_serializer(serializer):
    return getattr(
        serializer.Meta,
        'resource_name',
        get_resource_type_from_model(serializer.Meta.model))


def get_included_serializers(serializer):
    included_serializers = copy.copy(getattr(serializer, 'included_serializers', dict()))

    for name, value in six.iteritems(included_serializers):
        if not isinstance(value, type):
            if value == 'self':
                included_serializers[name] = serializer if isinstance(serializer, type) else serializer.__class__
            else:
                included_serializers[name] = import_class_from_dotted_path(value)

    return included_serializers


class Hyperlink(six.text_type):
    """
    A string like object that additionally has an associated name.
    We use this for hyperlinked URLs that may render as a named link
    in some contexts, or render as a plain URL in others.

    Comes from Django REST framework 3.2
    https://github.com/tomchristie/django-rest-framework
    """

    def __new__(self, url, name):
        ret = six.text_type.__new__(self, url)
        ret.name = name
        return ret

    is_hyperlink = True
