import inspect
import operator

import inflection
from django.conf import settings
from django.db.models import Manager
from django.db.models.fields.related_descriptors import (
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
)
from django.http import Http404
from django.utils import encoding
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, relations
from rest_framework.exceptions import APIException
from rest_framework.settings import api_settings

from .settings import json_api_settings

# Generic relation descriptor from django.contrib.contenttypes.
if "django.contrib.contenttypes" not in settings.INSTALLED_APPS:  # pragma: no cover
    # Target application does not use contenttypes. Importing would cause errors.
    ReverseGenericManyToOneDescriptor = object()
else:
    from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor


def get_resource_name(context, expand_polymorphic_types=False):
    """
    Return the name of a resource.
    """
    from rest_framework_json_api.serializers import PolymorphicModelSerializer

    view = context.get("view")

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
        if code.startswith("4") or code.startswith("5"):
            return "errors"

    try:
        resource_name = view.resource_name
    except AttributeError:
        try:
            if "kwargs" in context and "related_field" in context["kwargs"]:
                serializer = view.get_related_serializer_class()
            else:
                serializer = view.get_serializer_class()
            if expand_polymorphic_types and issubclass(
                serializer, PolymorphicModelSerializer
            ):
                return serializer.get_polymorphic_types()
            else:
                return get_resource_type_from_serializer(serializer)
        except AttributeError:
            try:
                resource_name = get_resource_type_from_model(view.model)
            except AttributeError:
                resource_name = view.__class__.__name__

            if not isinstance(resource_name, str):
                # The resource name is not a string - return as is
                return resource_name

            # the name was calculated automatically from the view > pluralize and format
            resource_name = format_resource_type(resource_name)

    return resource_name


def get_serializer_fields(serializer):
    fields = None
    if hasattr(serializer, "child"):
        fields = serializer.child.fields
        meta = getattr(serializer.child, "Meta", None)
    if hasattr(serializer, "fields"):
        fields = serializer.fields
        meta = getattr(serializer, "Meta", None)

    if fields is not None:
        meta_fields = getattr(meta, "meta_fields", {})
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
        return {format_value(key, format_type): value for key, value in obj.items()}

    return obj


def undo_format_field_names(obj):
    """
    Takes a dict and undo format field names to underscore which is the Python convention
    but only in case `JSON_API_FORMAT_FIELD_NAMES` is actually configured.
    """
    if json_api_settings.FORMAT_FIELD_NAMES:
        return format_field_names(obj, "underscore")

    return obj


def format_field_name(field_name):
    """
    Takes a field name and returns it with formatted keys as set in
    `JSON_API_FORMAT_FIELD_NAMES`
    """
    return format_value(field_name, json_api_settings.FORMAT_FIELD_NAMES)


def undo_format_field_name(field_name):
    """
    Takes a string and undos format field name to underscore which is the Python convention
    but only in case `JSON_API_FORMAT_FIELD_NAMES` is actually configured.
    """
    if json_api_settings.FORMAT_FIELD_NAMES:
        return format_value(field_name, "underscore")

    return field_name


def format_link_segment(value):
    """
    Takes a string value and returns it with formatted keys as set in `format_type`
    or `JSON_API_FORMAT_RELATED_LINKS`.

    :format_type: Either 'dasherize', 'camelize', 'capitalize' or 'underscore'
    """
    format_type = json_api_settings.FORMAT_RELATED_LINKS
    return format_value(value, format_type)


def undo_format_link_segment(value):
    """
    Takes a link segment and undos format link segment to underscore which is the Python
    convention but only in case `JSON_API_FORMAT_RELATED_LINKS` is actually configured.
    """

    if json_api_settings.FORMAT_RELATED_LINKS:
        return format_value(value, "underscore")

    return value


def format_value(value, format_type):
    if format_type == "dasherize":
        # inflection can't dasherize camelCase
        value = inflection.underscore(value)
        value = inflection.dasherize(value)
    elif format_type == "camelize":
        value = inflection.camelize(value, False)
    elif format_type == "capitalize":
        value = inflection.camelize(value)
    elif format_type == "underscore":
        value = inflection.underscore(value)
    return value


def format_resource_type(value, format_type=None, pluralize=None):
    if format_type is None:
        format_type = json_api_settings.FORMAT_TYPES

    if pluralize is None:
        pluralize = json_api_settings.PLURALIZE_TYPES

    if format_type:
        value = format_value(value, format_type)

    return inflection.pluralize(value) if pluralize else value


def get_related_resource_type(relation):
    from rest_framework_json_api.serializers import PolymorphicModelSerializer

    try:
        return get_resource_type_from_serializer(relation)
    except AttributeError:
        pass
    relation_model = None
    if hasattr(relation, "_meta"):
        relation_model = relation._meta.model
    elif hasattr(relation, "model"):
        # the model type was explicitly passed as a kwarg to ResourceRelatedField
        relation_model = relation.model
    elif hasattr(relation, "get_queryset") and relation.get_queryset() is not None:
        relation_model = relation.get_queryset().model
    elif hasattr(relation, "child_relation"):
        # For ManyRelatedField relationships, get the model from the child relationship
        try:
            return get_related_resource_type(relation.child_relation)
        except AttributeError:
            # Some read only relationships fail to get it directly, fall through to
            # get via the parent
            pass
    if not relation_model:
        parent_serializer = relation.parent
        parent_model = None
        if isinstance(parent_serializer, PolymorphicModelSerializer):
            parent_model = parent_serializer.get_polymorphic_serializer_for_instance(
                parent_serializer.instance
            ).Meta.model
        elif hasattr(parent_serializer, "Meta"):
            parent_model = getattr(parent_serializer.Meta, "model", None)
        elif hasattr(parent_serializer, "parent") and hasattr(
            parent_serializer.parent, "Meta"
        ):
            parent_model = getattr(parent_serializer.parent.Meta, "model", None)

        if parent_model is not None:
            if relation.source:
                if relation.source != "*":
                    parent_model_relation = getattr(parent_model, relation.source)
                else:
                    parent_model_relation = getattr(parent_model, relation.field_name)
            else:
                parent_model_relation = getattr(
                    parent_model, parent_serializer.field_name
                )

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
            elif hasattr(parent_model_relation, "field"):
                try:
                    relation_model = parent_model_relation.field.remote_field.model
                except AttributeError:
                    relation_model = parent_model_relation.field.related.model
            else:
                return get_related_resource_type(parent_model_relation)

    if relation_model is None:
        # For ManyRelatedFields on plain Serializers the resource_type
        # cannot be determined from a model, so we must get it from the
        # child_relation
        if hasattr(relation, "child_relation"):
            return get_related_resource_type(relation.child_relation)
        raise APIException(
            _(f"Could not resolve resource type for relation {relation}")
        )

    return get_resource_type_from_model(relation_model)


def get_resource_type_from_model(model):
    json_api_meta = getattr(model, "JSONAPIMeta", None)
    return getattr(json_api_meta, "resource_name", format_resource_type(model.__name__))


def get_resource_type_from_queryset(qs):
    return get_resource_type_from_model(qs.model)


def get_resource_type_from_instance(instance):
    if hasattr(instance, "_meta"):
        return get_resource_type_from_model(instance._meta.model)


def get_resource_type_from_manager(manager):
    return get_resource_type_from_model(manager.model)


def get_resource_type_from_serializer(serializer):
    json_api_meta = getattr(serializer, "JSONAPIMeta", None)
    meta = getattr(serializer, "Meta", None)
    if hasattr(json_api_meta, "resource_name"):
        return json_api_meta.resource_name
    elif hasattr(meta, "resource_name"):
        return meta.resource_name
    elif hasattr(meta, "model"):
        return get_resource_type_from_model(meta.model)
    raise AttributeError(
        f"can not detect 'resource_name' on serializer {serializer.__class__.__name__!r}"
        f" in module {serializer.__class__.__module__!r}"
    )


def get_resource_id(resource_instance, resource):
    """Returns the resource identifier for a given instance (`id` takes priority over `pk`)."""
    if resource and "id" in resource:
        return resource["id"] and encoding.force_str(resource["id"]) or None
    if resource_instance:
        return (
            hasattr(resource_instance, "pk")
            and encoding.force_str(resource_instance.pk)
            or None
        )
    return None


def get_included_resources(request, serializer=None):
    """Build a list of included resources."""
    include_resources_param = request.query_params.get("include") if request else None
    if include_resources_param:
        return include_resources_param.split(",")
    else:
        return get_default_included_resources_from_serializer(serializer)


def get_default_included_resources_from_serializer(serializer):
    meta = getattr(serializer, "JSONAPIMeta", None)
    if meta is None and getattr(serializer, "many", False):
        meta = getattr(serializer.child, "JSONAPIMeta", None)
    return list(getattr(meta, "included_resources", []))


def get_relation_instance(resource_instance, source, serializer):
    try:
        relation_instance = operator.attrgetter(source)(resource_instance)
    except AttributeError:
        # if the field is not defined on the model then we check the serializer
        # and if no value is there we skip over the field completely
        serializer_method = getattr(serializer, source, None)
        if serializer_method and callable(serializer_method):
            relation_instance = serializer_method(resource_instance)
        else:
            return False, None

    if isinstance(relation_instance, Manager):
        relation_instance = relation_instance.all()

    return True, relation_instance


def is_relationship_field(field):
    return isinstance(field, (relations.RelatedField, relations.ManyRelatedField))


class Hyperlink(str):
    """
    A string like object that additionally has an associated name.
    We use this for hyperlinked URLs that may render as a named link
    in some contexts, or render as a plain URL in others.

    Comes from Django REST framework 3.2
    https://github.com/tomchristie/django-rest-framework
    """

    def __new__(cls, url, name):
        ret = str.__new__(cls, url)
        ret.name = name
        return ret

    is_hyperlink = True


def format_drf_errors(response, context, exc):
    errors = []
    # handle generic errors. ValidationError('test') in a view for example
    if isinstance(response.data, list):
        for message in response.data:
            errors.extend(format_error_object(message, "/data", response))
    # handle all errors thrown from serializers
    else:
        # Avoid circular deps
        from rest_framework import generics

        has_serializer = isinstance(context["view"], generics.GenericAPIView)
        if has_serializer:
            serializer = context["view"].get_serializer()
            fields = get_serializer_fields(serializer) or dict()
            relationship_fields = [
                format_field_name(name)
                for name, field in fields.items()
                if is_relationship_field(field)
            ]

        for field, error in response.data.items():
            non_field_error = field == api_settings.NON_FIELD_ERRORS_KEY
            field = format_field_name(field)
            pointer = None
            if non_field_error:
                # Serializer error does not refer to a specific field.
                pointer = "/data"
            elif has_serializer:
                # pointer can be determined only if there's a serializer.
                rel = "relationships" if field in relationship_fields else "attributes"
                pointer = f"/data/{rel}/{field}"
            if isinstance(exc, Http404) and isinstance(error, str):
                # 404 errors don't have a pointer
                errors.extend(format_error_object(error, None, response))
            elif isinstance(error, str):
                classes = inspect.getmembers(exceptions, inspect.isclass)
                # DRF sets the `field` to 'detail' for its own exceptions
                if isinstance(exc, tuple(x[1] for x in classes)):
                    pointer = "/data"
                errors.extend(format_error_object(error, pointer, response))
            elif isinstance(error, list):
                errors.extend(format_error_object(error, pointer, response))
            else:
                errors.extend(format_error_object(error, pointer, response))

    context["view"].resource_name = "errors"
    response.data = errors

    return response


def format_error_object(message, pointer, response):
    errors = []
    if isinstance(message, dict):
        # as there is no required field in error object we check that all fields are string
        # except links, source or meta which might be a dict
        is_custom_error = all(
            [
                isinstance(value, str)
                for key, value in message.items()
                if key not in ["links", "source", "meta"]
            ]
        )

        if is_custom_error:
            if "source" not in message:
                message["source"] = {}
            if "pointer" not in message["source"]:
                message["source"]["pointer"] = pointer
            errors.append(message)
        else:
            for k, v in message.items():
                errors.extend(format_error_object(v, pointer + f"/{k}", response))
    elif isinstance(message, list):
        for num, error in enumerate(message):
            if isinstance(error, (list, dict)):
                new_pointer = pointer + f"/{num}"
            else:
                new_pointer = pointer
            if error:
                errors.extend(format_error_object(error, new_pointer, response))
    else:
        error_obj = {
            "detail": message,
            "status": encoding.force_str(response.status_code),
        }
        if pointer is not None:
            error_obj["source"] = {
                "pointer": pointer,
            }
        code = getattr(message, "code", None)
        if code is not None:
            error_obj["code"] = code
        errors.append(error_obj)

    return errors


def format_errors(data):
    if len(data) > 1 and isinstance(data, list):
        data.sort(key=lambda x: x.get("source", {}).get("pointer", ""))
    return {"errors": data}
