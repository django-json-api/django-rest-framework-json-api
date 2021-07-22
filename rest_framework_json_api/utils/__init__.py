import inspect
import logging
import operator
import warnings
from collections import OrderedDict

import inflection
from django.conf import settings
from django.db.models import Manager, Prefetch
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.db.models.query import QuerySet
from django.http import Http404
from django.utils import encoding
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.relations import RelatedField
from rest_framework.request import Request

from rest_framework_json_api.serializers import ModelSerializer, ValidationError

from .settings import json_api_settings

logger = logging.getLogger(__name__)

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
        resource_name = getattr(view, "resource_name")
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
        fields = getattr(serializer.child, "fields")
        meta = getattr(serializer.child, "Meta", None)
    if hasattr(serializer, "fields"):
        fields = getattr(serializer, "fields")
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
        formatted = OrderedDict()
        for key, value in obj.items():
            key = format_value(key, format_type)
            formatted[key] = value
        return formatted

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


def format_link_segment(value, format_type=None):
    """
    Takes a string value and returns it with formatted keys as set in `format_type`
    or `JSON_API_FORMAT_RELATED_LINKS`.

    :format_type: Either 'dasherize', 'camelize', 'capitalize' or 'underscore'
    """
    if format_type is None:
        format_type = json_api_settings.FORMAT_RELATED_LINKS
    else:
        warnings.warn(
            DeprecationWarning(
                "Using `format_type` argument is deprecated."
                "Use `format_value` instead."
            )
        )

    return format_value(value, format_type)


def undo_format_link_segment(value):
    """
    Takes a link segment and undos format link segment to underscore which is the Python convention
    but only in case `JSON_API_FORMAT_RELATED_LINKS` is actually configured.
    """

    if json_api_settings.FORMAT_RELATED_LINKS:
        return format_value(value, "underscore")

    return value


def format_value(value, format_type=None):
    if format_type is None:
        warnings.warn(
            DeprecationWarning(
                "Using `format_value` without passing on `format_type` argument is deprecated."
                "Use `format_field_name` instead."
            )
        )
        format_type = json_api_settings.FORMAT_FIELD_NAMES
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
    elif (
        getattr(relation, "many", False)
        and hasattr(relation.child, "Meta")
        and hasattr(relation.child.Meta, "model")
    ):
        # For ManyToMany relationships, get the model from the child
        # serializer of the list serializer
        relation_model = relation.child.Meta.model
    else:
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
            _("Could not resolve resource type for relation %s" % relation)
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
    raise AttributeError()


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


def get_included_serializers(serializer):
    warnings.warn(
        DeprecationWarning(
            "Using of `get_included_serializers(serializer)` function is deprecated."
            "Use `serializer.included_serializers` instead."
        )
    )

    return getattr(serializer, "included_serializers", dict())


def get_relation_instance(resource_instance, source, serializer):
    try:
        relation_instance = operator.attrgetter(source)(resource_instance)
    except AttributeError:
        # if the field is not defined on the model then we check the serializer
        # and if no value is there we skip over the field completely
        serializer_method = getattr(serializer, source, None)
        if serializer_method and hasattr(serializer_method, "__call__"):
            relation_instance = serializer_method(resource_instance)
        else:
            return False, None

    if isinstance(relation_instance, Manager):
        relation_instance = relation_instance.all()

    return True, relation_instance


class Hyperlink(str):
    """
    A string like object that additionally has an associated name.
    We use this for hyperlinked URLs that may render as a named link
    in some contexts, or render as a plain URL in others.

    Comes from Django REST framework 3.2
    https://github.com/tomchristie/django-rest-framework
    """

    def __new__(self, url, name):
        ret = str.__new__(self, url)
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
        for field, error in response.data.items():
            field = format_field_name(field)
            pointer = "/data/attributes/{}".format(field)
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
        # except links and source which might be a dict
        is_custom_error = all(
            [
                isinstance(value, str)
                for key, value in message.items()
                if key not in ["links", "source"]
            ]
        )

        if is_custom_error:
            if "source" not in message:
                message["source"] = {}
            message["source"] = {
                "pointer": pointer,
            }
            errors.append(message)
        else:
            for k, v in message.items():
                errors.extend(
                    format_error_object(v, pointer + "/{}".format(k), response)
                )
    elif isinstance(message, list):
        for num, error in enumerate(message):
            if isinstance(error, (list, dict)):
                new_pointer = pointer + "/{}".format(num)
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


def get_expensive_relational_fields(serializer_class: ModelSerializer) -> list[str]:
    """
    We define 'expensive' as relational fields on the serializer that don't correspond to a
    forward relation on the model.
    """
    return [
        field
        for field in getattr(serializer_class, 'included_serializers', {})
        if not isinstance(getattr(serializer_class.Meta.model, field, None), ForwardManyToOneDescriptor)
    ]


def get_cheap_relational_fields(serializer_class: ModelSerializer) -> list[str]:
    """
    We define 'cheap' as relational fields on the serializer that _do_ correspond to a
    forward relation on the model.
    """
    return [
        field
        for field in getattr(serializer_class, 'included_serializers', {})
        if isinstance(getattr(serializer_class.Meta.model, field, None), ForwardManyToOneDescriptor)
    ]


def get_queryset_for_field(field: RelatedField) -> QuerySet:
    model_field_descriptor = getattr(field.parent.Meta.model, field.field_name)
    # NOTE: Important to check in this order, as some of these classes are ancestors of one
    # another (ie `ManyToManyDescriptor` subclasses `ReverseManyToOneDescriptor`)
    if isinstance(model_field_descriptor, ForwardManyToOneDescriptor):
        if (qs := field.queryset) is None:
            qs = model_field_descriptor.field.related_model._default_manager
    elif isinstance(model_field_descriptor, ManyToManyDescriptor):
        qs = field.child_relation.queryset
    elif isinstance(model_field_descriptor, ReverseManyToOneDescriptor):
        if (qs := field.child_relation.queryset) is None:
            qs = model_field_descriptor.field.model._default_manager
    elif isinstance(model_field_descriptor, ReverseOneToOneDescriptor):
        qs = model_field_descriptor.get_queryset()

    # Note: We call `.all()` before returning, as `_default_manager` may on occasion return a Manager
    # instance rather than a QuerySet, and we strictly want to be working with the latter.
    # (_default_manager is being used both direclty by us here, and by drf behind the scenes)
    # See: https://github.com/encode/django-rest-framework/blame/master/rest_framework/utils/field_mapping.py#L243
    return qs.all()


def add_nested_prefetches_to_qs(
    serializer_class: ModelSerializer,
    qs: QuerySet,
    request: Request,
    sparsefields: dict[str, list[str]],
    includes: dict,  # TODO: Define typing as recursive once supported.
    select_related: str = '',
) -> QuerySet:
    """
    Prefetch all required data onto the supplied queryset, calling this method recursively for child
    serializers where needed.
    There is some added built-in optimisation here, attempting to opt for select_related calls over
    prefetches where possible -- it's only possible if the child serializers are interested
    exclusively in select_relating also. This is controlled with the `select_related` param.
    If `select_related` comes through, will attempt to instead build further onto this and return
    a dundered list of strings for the caller to use in a select_related call. If that fails,
    returns a qs as normal.
    """
    # Determine fields that'll be returned by this serializer.
    resource_name = get_resource_type_from_serializer(serializer_class)
    logger.debug(f'ADDING NESTED PREFETCHES FOR: {resource_name}')
    dummy_serializer = serializer_class(context={'request': request, 'demanded_fields': sparsefields.get(resource_name, [])})
    requested_fields = dummy_serializer.fields.keys()

    # Ensure any requested includes are in the fields list, else error loudly!
    if not includes.keys() <= requested_fields:
        errors = {f'{resource_name}.{field}': 'Field marked as include but not requested for serialization.' for field in includes.keys() - requested_fields}
        raise ValidationError(errors)

    included_serializers = get_included_serializers(serializer_class)

    # Iterate over all expensive relations and prefetch_related where needed.
    for field in get_expensive_relational_fields(serializer_class):
        if field in requested_fields:
            logger.debug(f'EXPENSIVE_FIELD: {field}')
            select_related = ''  # wipe, cannot be used. :(
            if not hasattr(qs.model, field):
                # We might fall into here if, for example, there's an expensive
                # SerializerMethodResourceRelatedField defined.
                continue
            if field in includes:
                logger.debug('- PREFETCHING DEEP')
                # Prefetch and recurse.
                child_serializer_class = included_serializers[field]
                prefetch_qs = add_nested_prefetches_to_qs(
                    child_serializer_class,
                    get_queryset_for_field(dummy_serializer.fields[field]),
                    request=request,
                    sparsefields=sparsefields,
                    includes=includes[field],
                )
                qs = qs.prefetch_related(Prefetch(field, prefetch_qs))
            else:
                logger.debug('- PREFETCHING SHALLOW')
                # Prefetch "shallowly"; we only care about ids.
                qs = qs.prefetch_related(field)  # TODO: Still use ResourceRelatedField.qs if present!

    # Iterate over all cheap (forward) relations and select_related (or prefetch) where needed.
    new_select_related = [select_related]
    for field in get_cheap_relational_fields(serializer_class):
        if field in requested_fields:
            logger.debug(f'CHEAP_FIELD: {field}')
            if field in includes:
                logger.debug('- present in includes')
                # Recurse and see if we get a prefetch qs back, or a select_related string.
                child_serializer_class = included_serializers[field]
                prefetch_qs_or_select_related_str = add_nested_prefetches_to_qs(
                    child_serializer_class,
                    get_queryset_for_field(dummy_serializer.fields[field]),
                    request=request,
                    sparsefields=sparsefields,
                    includes=includes[field],
                    select_related=field,
                )
                if isinstance(prefetch_qs_or_select_related_str, list):
                    logger.debug(f'SELECTING RELATED: {prefetch_qs_or_select_related_str}')
                    # Prefetch has come back as a list of (dundered) strings.
                    # We append onto existing select_related string, to potentially pass back up
                    # and also feed it directly into a select_related call in case the former
                    # falls through.
                    if select_related:
                        for sr in prefetch_qs_or_select_related_str:
                            new_select_related.append(f'{select_related}__{sr}')
                    qs = qs.select_related(*prefetch_qs_or_select_related_str)
                else:
                    # Select related option fell through, we need to do a prefetch. :(
                    logger.debug(f'PREFETCHING RELATED: {field}')
                    select_related = ''
                    qs = qs.prefetch_related(Prefetch(field, prefetch_qs_or_select_related_str))

    if select_related:
        return new_select_related
    return qs
