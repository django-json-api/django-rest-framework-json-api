"""
Utils.
"""
import copy

import inflection
from django.conf import settings
from django.utils import six, encoding
from django.utils.translation import ugettext_lazy as _
from rest_framework.compat import OrderedDict
from rest_framework.serializers import BaseSerializer, ListSerializer, ModelSerializer
from rest_framework.relations import RelatedField, HyperlinkedRelatedField, PrimaryKeyRelatedField, \
    HyperlinkedIdentityField
from rest_framework.settings import api_settings
from rest_framework.exceptions import APIException

try:
    from rest_framework.serializers import ManyRelatedField
except ImportError:
    ManyRelatedField = type(None)

try:
    from rest_framework_nested.relations import HyperlinkedRouterField
except ImportError:
    HyperlinkedRouterField = type(None)

import django

if django.VERSION < (1, 7):
    from django.utils.module_loading import import_by_path as import_class_from_dotted_path
else:
    from django.utils.module_loading import import_string as import_class_from_dotted_path


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
            serializer = getattr(view, 'serializer_class')
            return get_resource_type_from_serializer(serializer)
        except AttributeError:
            try:
                resource_name = view.model.__name__
            except AttributeError:
                resource_name = view.__class__.__name__

            if not isinstance(resource_name, six.string_types):
                # The resource name is not a string - return as is
                return resource_name

            # the name was calculated automatically from the view > pluralize and format
            resource_name = format_relation_name(resource_name)

    return resource_name


def get_serializer_fields(serializer):
    if hasattr(serializer, 'child'):
        return getattr(serializer.child, 'fields')
    if hasattr(serializer, 'fields'):
        return getattr(serializer, 'fields')


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


def build_json_resource_obj(fields, resource, resource_instance, resource_name):
    resource_data = [
        ('type', resource_name),
        ('id', encoding.force_text(resource_instance.pk) if resource_instance else None),
        ('attributes', extract_attributes(fields, resource)),
    ]
    relationships = extract_relationships(fields, resource, resource_instance)
    if relationships:
        resource_data.append(('relationships', relationships))
    # Add 'self' link if field is present and valid
    if api_settings.URL_FIELD_NAME in resource and \
            isinstance(fields[api_settings.URL_FIELD_NAME], RelatedField):
        resource_data.append(('links', {'self': resource[api_settings.URL_FIELD_NAME]}))
    return OrderedDict(resource_data)


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
            raise APIException('Unable to find related model for relation {relation}'.format(relation=relation))
    return format_relation_name(relation_model.__name__)


def get_instance_or_manager_resource_type(resource_instance_or_manager):
    if hasattr(resource_instance_or_manager, 'model'):
        return get_resource_type_from_manager(resource_instance_or_manager)
    if hasattr(resource_instance_or_manager, '_meta'):
        return get_resource_type_from_instance(resource_instance_or_manager)
    pass


def get_resource_type_from_queryset(qs):
    return format_relation_name(qs.model._meta.model.__name__)


def get_resource_type_from_instance(instance):
    return format_relation_name(instance._meta.model.__name__)


def get_resource_type_from_manager(manager):
    return format_relation_name(manager.model.__name__)


def get_resource_type_from_serializer(serializer):
    try:
        # Check the meta class for resource_name
        return serializer.Meta.resource_name
    except AttributeError:
        # Use the serializer model then pluralize and format
        return format_relation_name(serializer.Meta.model.__name__)


def extract_attributes(fields, resource):
    data = OrderedDict()
    for field_name, field in six.iteritems(fields):
        # ID is always provided in the root of JSON API so remove it from attributes
        if field_name == 'id':
            continue
        # Skip fields with relations
        if isinstance(field, (RelatedField, BaseSerializer, ManyRelatedField)):
            continue

        # Skip read_only attribute fields when the resource is non-existent
        # Needed for the "Raw data" form of the browseable API
        if resource.get(field_name) is None and fields[field_name].read_only:
            continue

        data.update({
            field_name: resource.get(field_name)
        })

    return format_keys(data)


def extract_relationships(fields, resource, resource_instance):
    # Avoid circular deps
    from rest_framework_json_api.relations import ResourceRelatedField

    data = OrderedDict()

    # Don't try to extract relationships from a non-existent resource
    if resource_instance is None:
        return

    for field_name, field in six.iteritems(fields):
        # Skip URL field
        if field_name == api_settings.URL_FIELD_NAME:
            continue

        # Skip fields without relations
        if not isinstance(field, (RelatedField, ManyRelatedField, BaseSerializer)):
            continue

        try:
            source = field.source
            relation_instance_or_manager = getattr(resource_instance, source)
        except AttributeError:
            # if the field is not defined on the model then we check the serializer
            # and if no value is there we skip over the field completely
            serializer_method = getattr(field.parent, source, None)
            if serializer_method and hasattr(serializer_method, '__call__'):
                relation_instance_or_manager = serializer_method(resource_instance)
            else:
                continue

        relation_type = get_related_resource_type(field)

        if isinstance(field, HyperlinkedIdentityField):
            # special case for HyperlinkedIdentityField
            relation_data = list()

            # Don't try to query an empty relation
            relation_queryset = relation_instance_or_manager.all() \
                if relation_instance_or_manager is not None else list()

            for related_object in relation_queryset:
                relation_data.append(
                    OrderedDict([('type', relation_type), ('id', encoding.force_text(related_object.pk))])
                )

            data.update({field_name: {
                'links': {
                    "related": resource.get(field_name)},
                'data': relation_data,
                'meta': {
                    'count': len(relation_data)
                }
            }})
            continue

        if isinstance(field, ResourceRelatedField):
            # special case for ResourceRelatedField
            relation_data = {
                'data': resource.get(field_name)
            }

            field_links = field.get_links(resource_instance)
            relation_data.update(
                {'links': field_links}
                if field_links else dict()
            )
            data.update({field_name: relation_data})
            continue

        if isinstance(field, (PrimaryKeyRelatedField, HyperlinkedRelatedField)):
            relation_id = relation_instance_or_manager.pk if resource.get(field_name) else None

            relation_data = {
                'data': (
                    OrderedDict([('type', relation_type), ('id', encoding.force_text(relation_id))])
                    if relation_id is not None else None)
            }

            relation_data.update(
                {'links': {'related': resource.get(field_name)}}
                if isinstance(field, HyperlinkedRelatedField) and resource.get(field_name) else dict()
            )
            data.update({field_name: relation_data})
            continue

        if isinstance(field, ManyRelatedField):

            if isinstance(field.child_relation, ResourceRelatedField):
                # special case for ResourceRelatedField
                relation_data = {
                    'data': resource.get(field_name)
                }

                field_links = field.child_relation.get_links(resource_instance)
                relation_data.update(
                    {'links': field_links}
                    if field_links else dict()
                )
                relation_data.update(
                    {
                        'meta': {
                            'count': len(resource.get(field_name))
                        }
                    }
                )
                data.update({field_name: relation_data})
                continue

            relation_data = list()
            for related_object in relation_instance_or_manager.all():
                related_object_type = get_instance_or_manager_resource_type(related_object)
                relation_data.append(OrderedDict([
                    ('type', related_object_type),
                    ('id', encoding.force_text(related_object.pk))
                ]))
            data.update({
                field_name: {
                    'data': relation_data,
                    'meta': {
                        'count': len(relation_data)
                    }
                }
            })
            continue

        if isinstance(field, ListSerializer):
            relation_data = list()

            serializer_data = resource.get(field_name)
            resource_instance_queryset = list(relation_instance_or_manager.all())
            if isinstance(serializer_data, list):
                for position in range(len(serializer_data)):
                    nested_resource_instance = resource_instance_queryset[position]
                    nested_resource_instance_type = get_resource_type_from_instance(nested_resource_instance)
                    relation_data.append(OrderedDict([
                        ('type', nested_resource_instance_type),
                        ('id', encoding.force_text(nested_resource_instance.pk))
                    ]))

                data.update({field_name: {'data': relation_data}})
                continue

        if isinstance(field, ModelSerializer):
            relation_model = field.Meta.model
            relation_type = format_relation_name(relation_model.__name__)

            data.update({
                field_name: {
                    'data': (
                        OrderedDict([
                            ('type', relation_type),
                            ('id', encoding.force_text(relation_instance_or_manager.pk))
                        ]) if resource.get(field_name) else None)
                }
            })
            continue

    return format_keys(data)


def extract_included(fields, resource, resource_instance, included_resources):
    # this function may be called with an empty record (example: Browsable Interface)
    if not resource_instance:
        return

    included_data = list()
    current_serializer = fields.serializer
    context = current_serializer.context
    included_serializers = get_included_serializers(current_serializer)
    included_resources = copy.copy(included_resources)

    for field_name, field in six.iteritems(fields):
        # Skip URL field
        if field_name == api_settings.URL_FIELD_NAME:
            continue

        # Skip fields without relations or serialized data
        if not isinstance(field, (RelatedField, ManyRelatedField, BaseSerializer)):
            continue

        try:
            included_resources.remove(field_name)
        except ValueError:
            # Skip fields not in requested included resources
            continue

        try:
            relation_instance_or_manager = getattr(resource_instance, field_name)
        except AttributeError:
            try:
                # For ManyRelatedFields if `related_name` is not set we need to access `foo_set` from `source`
                relation_instance_or_manager = getattr(resource_instance, field.child_relation.source)
            except AttributeError:
                serializer_method = getattr(current_serializer, field.source)
                relation_instance_or_manager = serializer_method(resource_instance)

        new_included_resources = [key.replace('%s.' % field_name, '', 1)
                                  for key in included_resources
                                  if field_name == key.split('.')[0]]
        serializer_data = resource.get(field_name)

        if isinstance(field, ManyRelatedField):
            serializer_class = included_serializers.get(field_name)
            field = serializer_class(relation_instance_or_manager.all(), many=True, context=context)
            serializer_data = field.data

        if isinstance(field, RelatedField):
            serializer_class = included_serializers.get(field_name)
            if relation_instance_or_manager is None:
                continue
            field = serializer_class(relation_instance_or_manager, context=context)
            serializer_data = field.data

        if isinstance(field, ListSerializer):
            serializer = field.child
            model = serializer.Meta.model
            relation_type = format_relation_name(model.__name__)
            relation_queryset = list(relation_instance_or_manager.all())

            # Get the serializer fields
            serializer_fields = get_serializer_fields(serializer)
            if serializer_data:
                for position in range(len(serializer_data)):
                    serializer_resource = serializer_data[position]
                    nested_resource_instance = relation_queryset[position]
                    included_data.append(
                        build_json_resource_obj(
                            serializer_fields, serializer_resource, nested_resource_instance, relation_type
                        )
                    )
                    included_data.extend(
                        extract_included(
                            serializer_fields, serializer_resource, nested_resource_instance, new_included_resources
                        )
                    )

        if isinstance(field, ModelSerializer):
            model = field.Meta.model
            relation_type = format_relation_name(model.__name__)

            # Get the serializer fields
            serializer_fields = get_serializer_fields(field)
            if serializer_data:
                included_data.append(
                    build_json_resource_obj(serializer_fields, serializer_data, relation_instance_or_manager,
                                            relation_type)
                )
                included_data.extend(
                    extract_included(
                        serializer_fields, serializer_data, relation_instance_or_manager, new_included_resources
                    )
                )

    return format_keys(included_data)


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
