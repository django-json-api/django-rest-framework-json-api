import copy
import inspect
import operator
import warnings
from collections import OrderedDict

import inflection
from django.conf import settings
from django.db.models import Manager
from django.db.models.fields.related_descriptors import (
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor
)
from django.utils import encoding, six
from django.utils.module_loading import import_string as import_class_from_dotted_path
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.serializers import ManyRelatedField  # noqa: F401

from .settings import json_api_settings

try:
    from rest_framework_nested.relations import HyperlinkedRouterField
except ImportError:
    HyperlinkedRouterField = object()

# Generic relation descriptor from django.contrib.contenttypes.
if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:  # pragma: no cover
    # Target application does not use contenttypes. Importing would cause errors.
    ReverseGenericManyToOneDescriptor = object()
else:
    from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor


def get_resource_name(context, expand_polymorphic_types=False):
    """
    Return the name of a resource.
    """
    from rest_framework_json_api.serializers import PolymorphicModelSerializer
    view = context.get('view')

    # Sanity check to make sure we have a view.
    if not view:
        return None

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
            if expand_polymorphic_types and issubclass(serializer, PolymorphicModelSerializer):
                return serializer.get_polymorphic_types()
            else:
                return get_resource_type_from_serializer(serializer)
        except AttributeError:
            try:
                resource_name = get_resource_type_from_model(view.model)
            except AttributeError:
                resource_name = view.__class__.__name__

            if not isinstance(resource_name, six.string_types):
                # The resource name is not a string - return as is
                return resource_name

            # the name was calculated automatically from the view > pluralize and format
            resource_name = format_resource_type(resource_name)

    return resource_name


def get_serializer_fields(serializer):
    fields = None
    if hasattr(serializer, 'child'):
        fields = getattr(serializer.child, 'fields')
        meta = getattr(serializer.child, 'Meta', None)
    if hasattr(serializer, 'fields'):
        fields = getattr(serializer, 'fields')
        meta = getattr(serializer, 'Meta', None)

    if fields is not None:
        meta_fields = getattr(meta, 'meta_fields', {})
        for field in meta_fields:
            try:
                fields.pop(field)
            except KeyError:
                pass
        return fields


def format_field_names(obj, format_type=None):
    """
    Takes a dict and returns it with formatted keys as set in `format_type`
    or `JSON_API_FORMAT_FIELD_NAMES`

    :format_type: Either 'dasherize', 'camelize', 'capitalize' or 'underscore'
    """
    if format_type is None:
        format_type = json_api_settings.FORMAT_FIELD_NAMES

    if isinstance(obj, dict):
        formatted = OrderedDict()
        for key, value in obj.items():
            key = format_value(key, format_type)
            formatted[key] = value
        return formatted

    return obj


def _format_object(obj, format_type=None):
    """Depending on settings calls either `format_keys` or `format_field_names`"""

    if json_api_settings.FORMAT_KEYS is not None:
        return format_keys(obj, format_type)

    return format_field_names(obj, format_type)


def format_keys(obj, format_type=None):
    """
    .. warning::

        `format_keys` function and `JSON_API_FORMAT_KEYS` setting are deprecated and will be
        removed in the future.
        Use `format_field_names` and `JSON_API_FORMAT_FIELD_NAMES` instead. Be aware that
        `format_field_names` only formats keys and preserves value.

    Takes either a dict or list and returns it with camelized keys only if
    JSON_API_FORMAT_KEYS is set.

    :format_type: Either 'dasherize', 'camelize', 'capitalize' or 'underscore'
    """
    warnings.warn(
        "`format_keys` function and `JSON_API_FORMAT_KEYS` setting are deprecated and will be "
        "removed in the future. "
        "Use `format_field_names` and `JSON_API_FORMAT_FIELD_NAMES` instead. Be aware that "
        "`format_field_names` only formats keys and preserves value.",
        DeprecationWarning
    )

    if format_type is None:
        format_type = json_api_settings.FORMAT_KEYS

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
        format_type = json_api_settings.format_type
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
    """
    .. warning::

        The 'format_relation_name' function has been renamed 'format_resource_type' and the
        settings are now 'JSON_API_FORMAT_TYPES' and 'JSON_API_PLURALIZE_TYPES' instead of
        'JSON_API_FORMAT_RELATION_KEYS' and 'JSON_API_PLURALIZE_RELATION_TYPE'
    """
    warnings.warn(
        "The 'format_relation_name' function has been renamed 'format_resource_type' and the "
        "settings are now 'JSON_API_FORMAT_TYPES' and 'JSON_API_PLURALIZE_TYPES' instead of "
        "'JSON_API_FORMAT_RELATION_KEYS' and 'JSON_API_PLURALIZE_RELATION_TYPE'",
        DeprecationWarning
    )
    if format_type is None:
        format_type = json_api_settings.FORMAT_RELATION_KEYS
    pluralize = json_api_settings.PLURALIZE_RELATION_TYPE
    return format_resource_type(value, format_type, pluralize)


def format_resource_type(value, format_type=None, pluralize=None):
    if format_type is None:
        format_type = json_api_settings.FORMAT_TYPES

    if pluralize is None:
        pluralize = json_api_settings.PLURALIZE_TYPES

    if format_type:
        # format_type will never be None here so we can use format_value
        value = format_value(value, format_type)

    return inflection.pluralize(value) if pluralize else value


def get_related_resource_type(relation):
    try:
        return get_resource_type_from_serializer(relation)
    except AttributeError:
        pass
    relation_model = None
    if hasattr(relation, '_meta'):
        relation_model = relation._meta.model
    elif hasattr(relation, 'model'):
        # the model type was explicitly passed as a kwarg to ResourceRelatedField
        relation_model = relation.model
    elif hasattr(relation, 'get_queryset') and relation.get_queryset() is not None:
        relation_model = relation.get_queryset().model
    elif (
            getattr(relation, 'many', False) and
            hasattr(relation.child, 'Meta') and
            hasattr(relation.child.Meta, 'model')):
        # For ManyToMany relationships, get the model from the child
        # serializer of the list serializer
        relation_model = relation.child.Meta.model
    else:
        parent_serializer = relation.parent
        parent_model = None
        if hasattr(parent_serializer, 'Meta'):
            parent_model = getattr(parent_serializer.Meta, 'model', None)
        elif hasattr(parent_serializer, 'parent') and hasattr(parent_serializer.parent, 'Meta'):
            parent_model = getattr(parent_serializer.parent.Meta, 'model', None)

        if parent_model is not None:
            if relation.source:
                if relation.source != '*':
                    parent_model_relation = getattr(parent_model, relation.source)
                else:
                    parent_model_relation = getattr(parent_model, relation.field_name)
            else:
                parent_model_relation = getattr(parent_model, parent_serializer.field_name)

            parent_model_relation_type = type(parent_model_relation)
            if parent_model_relation_type is ReverseManyToOneDescriptor:
                relation_model = parent_model_relation.rel.related_model
            elif parent_model_relation_type is ManyToManyDescriptor:
                relation_model = parent_model_relation.field.remote_field.model
                # In case we are in a reverse relation
                if relation_model == parent_model:
                    relation_model = parent_model_relation.field.model
            elif parent_model_relation_type is ReverseGenericManyToOneDescriptor:
                relation_model = parent_model_relation.rel.model
            elif hasattr(parent_model_relation, 'field'):
                try:
                    relation_model = parent_model_relation.field.remote_field.model
                except AttributeError:
                    relation_model = parent_model_relation.field.related.model
            else:
                return get_related_resource_type(parent_model_relation)

    if relation_model is None:
        raise APIException(_('Could not resolve resource type for relation %s' % relation))

    return get_resource_type_from_model(relation_model)


def get_resource_type_from_model(model):
    json_api_meta = getattr(model, 'JSONAPIMeta', None)
    return getattr(
        json_api_meta,
        'resource_name',
        format_resource_type(model.__name__))


def get_resource_type_from_queryset(qs):
    return get_resource_type_from_model(qs.model)


def get_resource_type_from_instance(instance):
    if hasattr(instance, '_meta'):
        return get_resource_type_from_model(instance._meta.model)


def get_resource_type_from_manager(manager):
    return get_resource_type_from_model(manager.model)


def get_resource_type_from_serializer(serializer):
    json_api_meta = getattr(serializer, 'JSONAPIMeta', None)
    meta = getattr(serializer, 'Meta', None)
    if hasattr(json_api_meta, 'resource_name'):
        return json_api_meta.resource_name
    elif hasattr(meta, 'resource_name'):
        return meta.resource_name
    elif hasattr(meta, 'model'):
        return get_resource_type_from_model(meta.model)
    raise AttributeError()


def get_included_resources(request, serializer=None):
    """ Build a list of included resources. """
    include_resources_param = request.query_params.get('include') if request else None
    if include_resources_param:
        return include_resources_param.split(',')
    else:
        return get_default_included_resources_from_serializer(serializer)


def get_default_included_resources_from_serializer(serializer):
    meta = getattr(serializer, 'JSONAPIMeta', None)
    if meta is None and getattr(serializer, 'many', False):
        meta = getattr(serializer.child, 'JSONAPIMeta', None)
    return list(getattr(meta, 'included_resources', []))


def get_included_serializers(serializer):
    included_serializers = copy.copy(getattr(serializer, 'included_serializers', dict()))

    for name, value in six.iteritems(included_serializers):
        if not isinstance(value, type):
            if value == 'self':
                included_serializers[name] = (
                    serializer if isinstance(serializer, type) else serializer.__class__
                )
            else:
                included_serializers[name] = import_class_from_dotted_path(value)

    return included_serializers


def get_relation_instance(resource_instance, source, serializer):
    try:
        relation_instance = operator.attrgetter(source)(resource_instance)
    except AttributeError:
        # if the field is not defined on the model then we check the serializer
        # and if no value is there we skip over the field completely
        serializer_method = getattr(serializer, source, None)
        if serializer_method and hasattr(serializer_method, '__call__'):
            relation_instance = serializer_method(resource_instance)
        else:
            return False, None

    if isinstance(relation_instance, Manager):
        relation_instance = relation_instance.all()

    return True, relation_instance


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


def format_drf_errors(response, context, exc):
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


def format_errors(data):
    if len(data) > 1 and isinstance(data, list):
        data.sort(key=lambda x: x.get('source', {}).get('pointer', ''))
    return {'errors': data}
