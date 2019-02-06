from collections import Iterable

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor
)
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.urls import NoReverseMatch
from django.utils.module_loading import import_string as import_class_from_dotted_path
from rest_framework import generics, viewsets
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.fields import get_attribute
from rest_framework.relations import PKOnlyObject
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer, SkipField

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework_json_api.utils import (
    Hyperlink,
    OrderedDict,
    get_included_resources,
    get_resource_type_from_instance
)


class PrefetchForIncludesHelperMixin(object):
    def get_queryset(self):
        """
        This viewset provides a helper attribute to prefetch related models
        based on the include specified in the URL.

        __all__ can be used to specify a prefetch which should be done regardless of the include

        .. code:: python

            # When MyViewSet is called with ?include=author it will prefetch author and authorbio
            class MyViewSet(viewsets.ModelViewSet):
                queryset = Book.objects.all()
                prefetch_for_includes = {
                    '__all__': [],
                    'author': ['author', 'author__authorbio'],
                    'category.section': ['category']
                }
        """
        qs = super(PrefetchForIncludesHelperMixin, self).get_queryset()
        if not hasattr(self, 'prefetch_for_includes'):
            return qs

        includes = self.request.GET.get('include', '').split(',')
        for inc in includes + ['__all__']:
            prefetches = self.prefetch_for_includes.get(inc)
            if prefetches:
                qs = qs.prefetch_related(*prefetches)

        return qs


class AutoPrefetchMixin(object):
    def get_queryset(self, *args, **kwargs):
        """ This mixin adds automatic prefetching for OneToOne and ManyToMany fields. """
        qs = super(AutoPrefetchMixin, self).get_queryset(*args, **kwargs)
        included_resources = get_included_resources(self.request)

        for included in included_resources:
            included_model = None
            levels = included.split('.')
            level_model = qs.model
            for level in levels:
                if not hasattr(level_model, level):
                    break
                field = getattr(level_model, level)
                field_class = field.__class__

                is_forward_relation = (
                    issubclass(field_class, ForwardManyToOneDescriptor) or
                    issubclass(field_class, ManyToManyDescriptor)
                )
                is_reverse_relation = (
                    issubclass(field_class, ReverseManyToOneDescriptor) or
                    issubclass(field_class, ReverseOneToOneDescriptor)
                )
                if not (is_forward_relation or is_reverse_relation):
                    break

                if level == levels[-1]:
                    included_model = field
                else:

                    if issubclass(field_class, ReverseOneToOneDescriptor):
                        model_field = field.related.field
                    else:
                        model_field = field.field

                    if is_forward_relation:
                        level_model = model_field.related_model
                    else:
                        level_model = model_field.model

            if included_model is not None:
                qs = qs.prefetch_related(included.replace('.', '__'))

        return qs


class RelatedMixin(object):
    """
    This mixin handles all related entities, whose Serializers are declared in "related_serializers"
    """

    def retrieve_related(self, request, *args, **kwargs):
        serializer_kwargs = {}
        instance = self.get_related_instance()

        if hasattr(instance, 'all'):
            instance = instance.all()

        if callable(instance):
            instance = instance()

        if instance is None:
            return Response(data=None)

        if isinstance(instance, Iterable):
            serializer_kwargs['many'] = True

        serializer = self.get_serializer(instance, **serializer_kwargs)
        return Response(serializer.data)

    def get_serializer_class(self):
        parent_serializer_class = super(RelatedMixin, self).get_serializer_class()

        if 'related_field' in self.kwargs:
            field_name = self.kwargs['related_field']

            # Try get the class from related_serializers
            if hasattr(parent_serializer_class, 'related_serializers'):
                _class = parent_serializer_class.related_serializers.get(field_name, None)
                if _class is None:
                    raise NotFound

            elif hasattr(parent_serializer_class, 'included_serializers'):
                _class = parent_serializer_class.included_serializers.get(field_name, None)
                if _class is None:
                    raise NotFound

            else:
                assert False, \
                    'Either "included_serializers" or "related_serializers" should be configured'

            if not isinstance(_class, type):
                return import_class_from_dotted_path(_class)
            return _class

        return parent_serializer_class

    def get_related_field_name(self):
        return self.kwargs['related_field']

    def get_related_instance(self):
        parent_obj = self.get_object()
        parent_serializer = self.serializer_class(parent_obj)
        field_name = self.get_related_field_name()
        field = parent_serializer.fields.get(field_name, None)

        if field is not None:
            try:
                instance = field.get_attribute(parent_obj)
            except SkipField:
                instance = get_attribute(parent_obj, field.source_attrs)
            else:
                if isinstance(instance, PKOnlyObject):
                    # need whole object
                    instance = get_attribute(parent_obj, field.source_attrs)
            return instance
        else:
            try:
                return getattr(parent_obj, field_name)
            except AttributeError:
                raise NotFound


class ModelViewSet(AutoPrefetchMixin,
                   PrefetchForIncludesHelperMixin,
                   RelatedMixin,
                   viewsets.ModelViewSet):
    pass


class ReadOnlyModelViewSet(AutoPrefetchMixin,
                           PrefetchForIncludesHelperMixin,
                           RelatedMixin,
                           viewsets.ReadOnlyModelViewSet):
    pass


class RelationshipView(generics.GenericAPIView):
    serializer_class = ResourceIdentifierObjectSerializer
    self_link_view_name = None
    related_link_view_name = None
    field_name_mapping = {}

    def get_serializer_class(self):
        if getattr(self, 'action', False) is None:
            return Serializer
        return self.serializer_class

    def __init__(self, **kwargs):
        super(RelationshipView, self).__init__(**kwargs)
        # We include this simply for dependency injection in tests.
        # We can't add it as a class attributes or it would expect an
        # implicit `self` argument to be passed.
        self.reverse = reverse

    def get_url(self, name, view_name, kwargs, request):
        """
        Given a name, view name and kwargs, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """

        # Return None if the view name is not supplied
        if not view_name:
            return None

        # Return the hyperlink, or error if incorrectly configured.
        try:
            url = self.reverse(view_name, kwargs=kwargs, request=request)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise ImproperlyConfigured(msg % view_name)

        if url is None:
            return None

        return Hyperlink(url, name)

    def get_links(self):
        return_data = OrderedDict()
        self_link = self.get_url('self', self.self_link_view_name, self.kwargs, self.request)
        related_kwargs = {self.lookup_field: self.kwargs.get(self.lookup_field)}
        related_link = self.get_url(
            'related', self.related_link_view_name, related_kwargs, self.request
        )
        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data

    def get(self, request, *args, **kwargs):
        related_instance = self.get_related_instance()
        serializer_instance = self._instantiate_serializer(related_instance)
        return Response(serializer_instance.data)

    def remove_relationships(self, instance_manager, field):
        field_object = getattr(instance_manager, field)

        if field_object.null:
            for obj in instance_manager.all():
                setattr(obj, field_object.name, None)
                obj.save()
        else:
            instance_manager.all().delete()

        return instance_manager

    def patch(self, request, *args, **kwargs):
        parent_obj = self.get_object()
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, Manager):
            related_model_class = related_instance_or_manager.model
            serializer = self.get_serializer(
                data=request.data, model_class=related_model_class, many=True
            )
            serializer.is_valid(raise_exception=True)

            # for to one
            if hasattr(related_instance_or_manager, "field"):
                related_instance_or_manager = self.remove_relationships(
                    instance_manager=related_instance_or_manager, field="field")
            # for to many
            else:
                related_instance_or_manager = self.remove_relationships(
                    instance_manager=related_instance_or_manager, field="target_field")

            # have to set bulk to False since data isn't saved yet
            class_name = related_instance_or_manager.__class__.__name__
            if class_name != 'ManyRelatedManager':
                related_instance_or_manager.add(*serializer.validated_data, bulk=False)
            else:
                related_instance_or_manager.add(*serializer.validated_data)
        else:
            related_model_class = related_instance_or_manager.__class__
            serializer = self.get_serializer(data=request.data, model_class=related_model_class)
            serializer.is_valid(raise_exception=True)
            setattr(parent_obj, self.get_related_field_name(), serializer.validated_data)
            parent_obj.save()
            related_instance_or_manager = self.get_related_instance()  # Refresh instance
        result_serializer = self._instantiate_serializer(related_instance_or_manager)
        return Response(result_serializer.data)

    def post(self, request, *args, **kwargs):
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, Manager):
            related_model_class = related_instance_or_manager.model
            serializer = self.get_serializer(
                data=request.data, model_class=related_model_class, many=True
            )
            serializer.is_valid(raise_exception=True)
            if frozenset(serializer.validated_data) <= frozenset(related_instance_or_manager.all()):
                return Response(status=204)
            related_instance_or_manager.add(*serializer.validated_data)
        else:
            raise MethodNotAllowed('POST')
        result_serializer = self._instantiate_serializer(related_instance_or_manager)
        return Response(result_serializer.data)

    def delete(self, request, *args, **kwargs):
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, Manager):
            related_model_class = related_instance_or_manager.model
            serializer = self.get_serializer(
                data=request.data, model_class=related_model_class, many=True
            )
            serializer.is_valid(raise_exception=True)
            objects = related_instance_or_manager.all()
            if frozenset(serializer.validated_data).isdisjoint(frozenset(objects)):
                return Response(status=204)
            try:
                related_instance_or_manager.remove(*serializer.validated_data)
            except AttributeError:
                raise Conflict(
                    'This object cannot be removed from this relationship without being '
                    'added to another'
                )
        else:
            raise MethodNotAllowed('DELETE')
        result_serializer = self._instantiate_serializer(related_instance_or_manager)
        return Response(result_serializer.data)

    def get_related_instance(self):
        try:
            return getattr(self.get_object(), self.get_related_field_name())
        except AttributeError:
            raise NotFound

    def get_related_field_name(self):
        field_name = self.kwargs['related_field']
        if field_name in self.field_name_mapping:
            return self.field_name_mapping[field_name]
        return field_name

    def _instantiate_serializer(self, instance):
        if isinstance(instance, Model) or instance is None:
            return self.get_serializer(instance=instance)
        else:
            if isinstance(instance, (QuerySet, Manager)):
                instance = instance.all()

            return self.get_serializer(instance=instance, many=True)

    def get_resource_name(self):
        if not hasattr(self, '_resource_name'):
            instance = getattr(self.get_object(), self.get_related_field_name())
            self._resource_name = get_resource_type_from_instance(instance)
        return self._resource_name

    def set_resource_name(self, value):
        self._resource_name = value

    resource_name = property(get_resource_name, set_resource_name)
