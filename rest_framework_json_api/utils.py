"""
Utils.
"""
import inflection
from django.core import urlresolvers
from django.conf import settings
from django.utils import six, encoding
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import BaseSerializer, ListSerializer, ModelSerializer
from rest_framework.relations import RelatedField, HyperlinkedRelatedField, PrimaryKeyRelatedField, \
    HyperlinkedIdentityField
from rest_framework.settings import api_settings
from rest_framework.exceptions import APIException

from django.utils.six.moves.urllib.parse import urlparse

try:
    from rest_framework.compat import OrderedDict
except ImportError:
    OrderedDict = dict

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
            # Check the meta class
            resource_name = (getattr(view, 'serializer_class').Meta.resource_name)
        except AttributeError:
            # Use the model
            try:
                resource_name = (getattr(view, 'serializer_class').Meta.model.__name__)
            except AttributeError:
                try:
                    resource_name = view.model.__name__
                except AttributeError:
                    resource_name = view.__class__.__name__

            # if the name was calculated automatically then pluralize and format
            if not isinstance(resource_name, six.string_types):
                return resource_name

            resource_name = inflection.pluralize(resource_name.lower())

            resource_name = format_value(resource_name)

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


def format_value(value, format_type=None):
    format_type = getattr(settings, 'JSON_API_FORMAT_KEYS', False)
    if format_type == 'dasherize':
        value = inflection.dasherize(value)
    elif format_type == 'camelize':
        value = inflection.camelize(value)
    elif format_type == 'underscore':
        value = inflection.underscore(value)
    return value


def build_json_resource_obj(fields, resource, resource_instance, resource_name):
    resource_data = [
        ('type', resource_name),
        ('id', encoding.force_text(resource_instance.pk)),
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
    if hasattr(relation, 'get_queryset') and relation.get_queryset() is not None:
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
            relation_model = parent_model_relation.related.model
        elif hasattr(parent_model_relation, 'field'):
            relation_model = parent_model_relation.field.related.model
        else:
            raise APIException('Unable to find related model for relation {relation}'.format(relation=relation))
    return inflection.pluralize(relation_model.__name__).lower()


def extract_attributes(fields, resource):
    data = OrderedDict()
    for field_name, field in six.iteritems(fields):
        # ID is always provided in the root of JSON API so remove it from attributes
        if field_name == 'id':
            continue
        # Skip fields with relations
        if isinstance(field, (RelatedField, BaseSerializer, ManyRelatedField)):
            continue
        data.update({
            field_name: resource.get(field_name)
        })

    return format_keys(data)


def extract_relationships(fields, resource, resource_instance):
    data = OrderedDict()
    for field_name, field in six.iteritems(fields):
        # Skip URL field
        if field_name == api_settings.URL_FIELD_NAME:
            continue

        # Skip fields without relations
        if not isinstance(field, (RelatedField, ManyRelatedField, BaseSerializer)):
            continue

        relation_type = get_related_resource_type(field)

        if isinstance(field, HyperlinkedIdentityField):
            # special case for HyperlinkedIdentityField
            relation_data = list()
            relation_manager = getattr(resource_instance, field_name)
            # Don't try to query an empty relation
            related = relation_manager.all() if relation_manager is not None else list()
            for relation in related:
                relation_data.append(OrderedDict([('type', relation_type), ('id', encoding.force_text(relation.pk))]))

            data.update({field_name: {
                'links': {
                    "related": resource.get(field_name)},
                'data': relation_data,
                'meta': {
                    'count': len(relation_data)
                }
            }})
            continue

        if isinstance(field, (PrimaryKeyRelatedField, HyperlinkedRelatedField)):
            relation_id = getattr(resource_instance, field_name).pk if resource.get(field_name) else None

            relation_data = {
                'data': (OrderedDict([
                    ('type', relation_type), ('id', encoding.force_text(relation_id))
                ]) if relation_id is not None else None)
            }

            relation_data.update(
                {'links': {'related': resource.get(field_name)}}
                if isinstance(field, HyperlinkedRelatedField) and resource.get(field_name) else {}
            )
            data.update({field_name: relation_data})
            continue

        if isinstance(field, ManyRelatedField):
            relation_data = list()
            relation = field.child_relation
            relation_type = get_related_resource_type(relation)
            for related_object in getattr(resource_instance, field_name).all():
                relation_data.append(OrderedDict([
                    ('type', relation_type),
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
            serializer = field.child
            relation_model = serializer.Meta.model
            relation_type = inflection.pluralize(relation_model.__name__).lower()

            serializer_data = resource.get(field_name)
            resource_instance_queryset = getattr(resource_instance, field_name).all()
            if isinstance(serializer_data, list):
                for position in range(len(serializer_data)):
                    nested_resource_instance = resource_instance_queryset[position]
                    relation_data.append(
                        OrderedDict([
                            ('type', relation_type), ('id', encoding.force_text(nested_resource_instance.pk))
                        ]))

                data.update({field_name: {'data': relation_data}})
                continue

        if isinstance(field, ModelSerializer):
            relation_model = field.Meta.model
            relation_type = inflection.pluralize(relation_model.__name__).lower()

            data.update({
                field_name: {
                    'data': (
                        OrderedDict([
                            ('type', relation_type),
                            ('id', encoding.force_text(getattr(resource_instance, field_name).pk))
                        ]) if resource.get(field_name) else None)
                }
            })
            continue

    return format_keys(data)


def extract_included(fields, resource, resource_instance):
    included_data = list()
    for field_name, field in six.iteritems(fields):
        # Skip URL field
        if field_name == api_settings.URL_FIELD_NAME:
            continue

        # Skip fields without serialized data
        if not isinstance(field, BaseSerializer):
            continue

        if isinstance(field, ListSerializer):

            serializer = field.child
            model = serializer.Meta.model
            relation_type = inflection.pluralize(model.__name__).lower()

            # Get the serializer fields
            serializer_fields = get_serializer_fields(serializer)
            serializer_data = resource.get(field_name)
            if isinstance(serializer_data, list):
                for position in range(len(serializer_data)):
                    serializer_resource = serializer_data[position]
                    resource_instance_manager = getattr(resource_instance, field_name).all()
                    nested_resource_instance = resource_instance_manager[position]
                    included_data.append(
                        build_json_resource_obj(
                            serializer_fields, serializer_resource, nested_resource_instance, relation_type
                        )
                    )

        if isinstance(field, ModelSerializer):

            model = field.Meta.model
            relation_type = inflection.pluralize(model.__name__).lower()

            # Get the serializer fields
            serializer_fields = get_serializer_fields(field)
            serializer_data = resource.get(field_name)
            nested_resource_instance = getattr(resource_instance, field_name).all()
            if serializer_data:
                included_data.append(
                    build_json_resource_obj(serializer_fields, serializer_data, nested_resource_instance, relation_type)
                )

    return format_keys(included_data)
