"""
Utils.
"""
import inflection


from django.core import urlresolvers
from django.conf import settings
from django.utils import six, encoding
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.utils.translation import ugettext_lazy as _

from rest_framework import relations, serializers
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

try:
    from rest_framework.serializers import ListSerializer
except ImportError:
    ListSerializer = type(None)


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


def convert_to_text(resource, field, field_name, request):
    data = dict()

    data[field_name] = encoding.force_text(resource[field_name])

    return {
        "data": data,
    }


def rename_to_href(resource, field, field_name, request):
    data = dict()

    data["links"] = dict()
    data["links"]["self"] = resource[field_name]

    return {
        "data": data,
    }


def get_related_field(field):
    if isinstance(field, ManyRelatedField):
        return field.child_relation

    if isinstance(field, ListSerializer):
        return field.child

    return field


def is_related_many(field):
    if hasattr(field, "many"):
        return field.many

    if isinstance(field, ManyRelatedField):
        return True

    if isinstance(field, ListSerializer):
        return True

    return False


def model_from_obj(obj):
    model = getattr(obj, "model", None)

    if model is not None:
        return model

    queryset = getattr(obj, "queryset", None)

    if queryset is not None:
        return queryset.model

    return None


def model_to_resource_type(model):
    """
    Return the verbose plural form of a model name, with underscores

    Examples:
    Person -> "people"
    ProfileImage -> "profile_image"
    """
    if model is None:
        return "data"

    return encoding.force_text(model._meta.verbose_name_plural)


def handle_nested_serializer(resource, field, field_name, request):
    serializer_field = get_related_field(field)

    if hasattr(serializer_field, "opts"):
        model = serializer_field.opts.model
    else:
        model = serializer_field.Meta.model

    resource_type = model_to_resource_type(model)

    linked_ids = dict()
    links = dict()
    linked = dict()
    linked[resource_type] = []

    if is_related_many(field):
        items = resource[field_name]
    else:
        items = [resource[field_name]]

    obj_ids = []

    resource.serializer = serializer_field

    for item in items:
        converted = convert_resource(item, resource, request)
        linked_obj = converted["data"]
        linked_ids = converted.pop("linked_ids", {})

        if linked_ids:
            linked_obj["links"] = linked_ids

        # FIXME: need to add nested ids to obj_ids
        # obj_ids.append(converted["data"]["id"])

        # field_links = prepend_links_with_name(
        #     converted.get("links", {}), resource_type)
        field_links = dict()

        field_links[field_name] = {
            "type": resource_type,
        }

        if "href" in converted["data"]:
            url_field_name = api_settings.URL_FIELD_NAME
            url_field = serializer_field.fields[url_field_name]

            field_links[field_name]["href"] = url_to_template(
                url_field.view_name, request, field_name,
            )

        links.update(field_links)

        linked[resource_type].append(linked_obj)

    if is_related_many(field):
        linked_ids[field_name] = obj_ids
    else:
        linked_ids[field_name] = obj_ids[0]

    return {"linked_ids": linked_ids, "links": links, "linked": linked}


def handle_related_field(resource, field, field_name, request):
    related_field = get_related_field(field)

    model = model_from_obj(related_field)
    resource_type = model_to_resource_type(model)

    linkage = None

    if field_name in resource:
        if is_related_many(field):
            linkage = []

            pks = [encoding.force_text(pk) for pk in resource[field_name]]
            for pk in pks:
                link = {
                    "type": resource_type,
                    "id": pk,
                }
                linkage.append(link)
        elif resource[field_name]:
            linkage = {
                "type": resource_type,
                "id": encoding.force_text(resource[field_name]),
            }

    return {
        "data": {
            "links": {
                field_name: {
                    "linkage": linkage,
                },
            },
        },
    }


def handle_url_field(resource, field, field_name, request):
    if field_name not in resource:
        return {}

    related_field = get_related_field(field)

    model = model_from_obj(related_field)
    resource_type = model_to_resource_type(model)

    linkage = None

    pks = url_to_pk(resource[field_name], field)

    if not isinstance(pks, list):
        if pks:
            linkage = {
                "type": resource_type,
                "id": pks,
            }
    else:
        linkage = []

        for pk in pks:
            link = {
                "type": resource_type,
                "id": pk,
            }

            linkage.append(link)

    return {
        "data": {
            "links": {
                field_name: {
                    "linkage": linkage,
                },
            },
        },
    }


def url_to_pk(url_data, field):
    if is_related_many(field):
        try:
            obj_list = field.to_internal_value(url_data)
        except AttributeError:
            obj_list = [field.from_native(url) for url in url_data]

        return [encoding.force_text(obj.pk) for obj in obj_list]

    if url_data:
        try:
            obj = field.to_internal_value(url_data)
        except AttributeError:
            obj = field.from_native(url_data)

        return encoding.force_text(obj.pk)
    else:
        return None


def url_to_template(view_name, request, template_name):
    resolver = urlresolvers.get_resolver(None)
    info = resolver.reverse_dict[view_name]

    path_template = info[0][0][0]
    # FIXME: what happens when URL has more than one dynamic values?
    # e.g. nested relations: manufacturer/%(id)s/cars/%(card_id)s
    path = path_template % {info[0][0][1][0]: '{%s}' % template_name}

    parsed_url = urlparse(request.build_absolute_uri())

    return urlunparse(
        [parsed_url.scheme, parsed_url.netloc, path, '', '', '']
    )


def fields_from_resource(resource, data):
    if hasattr(data, "serializer"):
        resource = data.serializer

        if hasattr(resource, "child"):
            resource = resource.child

    return getattr(resource, "fields", None)


def update_nested(original, update):
    for key, value in update.items():
        if key in original:
            if isinstance(original[key], list):
                original[key].extend(update[key])
            elif isinstance(original[key], dict):
                original[key].update(update[key])
        else:
            original[key] = value

    return original


def convert_resource(resource, resource_data, request):
    convert_by_name = {
        'id': convert_to_text,
        api_settings.URL_FIELD_NAME: rename_to_href,
    }
    convert_by_type = {
        relations.PrimaryKeyRelatedField: handle_related_field,
        relations.HyperlinkedRelatedField: handle_url_field,
        serializers.ModelSerializer: handle_nested_serializer,
    }

    fields = fields_from_resource(resource, resource_data)

    if not fields:
        raise AttributeError('Resource must have a fields attribute.')

    data = dict()
    included = dict()
    meta = dict()

    for field_name, field in six.iteritems(fields):
        converted = None

        if field_name in convert_by_name:
            converter = convert_by_name[field_name]
            converted = converter(resource, field, field_name, request)
        else:
            related_field = get_related_field(field)

            for field_type, converter in \
                    six.iteritems(convert_by_type):
                if isinstance(related_field, field_type):
                    converted = converter(
                        resource, field, field_name, request)
                    break

        if converted:
            data = update_nested(
                data,
                converted.pop("data", {})
            )
            included = update_nested(
                included,
                converted.get("included", {})
            )
            meta = update_nested(
                meta,
                converted.get("meta", {})
            )
        else:
            data[field_name] = resource[field_name]

    if hasattr(resource, "serializer"):
        serializer = resource.serializer
        model = serializer.Meta.model

        resource_type = model_to_resource_type(model)

        data["type"] = resource_type

    return {
        "data": data,
        "included": included,
        "meta": meta,
    }