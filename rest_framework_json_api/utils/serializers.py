import logging

from django.db.models import Prefetch
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.db.models.query import QuerySet
from rest_framework.relations import RelatedField
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer, ValidationError

from rest_framework_json_api.utils import (
    get_included_serializers,
    get_resource_type_from_serializer,
)

logger = logging.getLogger(__name__)


def get_expensive_relational_fields(serializer_class) -> list[str]:
    """
    We define 'expensive' as relational fields on the serializer that don't correspond to a
    forward relation on the model.
    """
    return [
        field
        for field in getattr(serializer_class, 'included_serializers', {})
        if not isinstance(getattr(serializer_class.Meta.model, field, None), ForwardManyToOneDescriptor)
    ]


def get_cheap_relational_fields(serializer_class) -> list[str]:
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
