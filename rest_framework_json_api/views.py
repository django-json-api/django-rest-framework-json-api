import re
from collections.abc import Iterable

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
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
    get_resource_type_from_instance,
    includes_to_dict,
    undo_format_link_segment,
)

from .utils.serializers import get_expensive_relational_fields


class AutoPrefetchMixin(object):
    """ Hides "expensive" fields by default, and calculates automatic prefetching when said fields
        are explicitly requested.

        "Expensive" fields are ones that require additional SQL queries to prepare, such as
        reverse or M2M relations.
    """
    def __init_subclass__(cls, **kwargs):
        """Run a smidge of validation at class declaration, to avoid silly mistakes."""

        # Throw error if a `prefetch_for_includes` is defined.
        if hasattr(cls, 'prefetch_for_includes'):
            raise AttributeError(
                f"{cls.__name__!r} defines `prefetch_for_includes`. This manual legacy form of"
                " prefetching is no longer supported! It's all automatically handled now."
            )
        # Throw error if a `select_for_includes` is defined.
        if hasattr(cls, 'select_for_includes'):
            raise AttributeError(
                f"{cls.__name__!r} defines `select_for_includes`. This manual legacy form of"
                " prefetching is no longer supported! It's all automatically handled now."
            )

        return super().__init_subclass__(**kwargs)

    def get_sparsefields_as_dict(self):
        if not hasattr(self, '_sparsefields'):
            self._sparsefields = {
                match.groupdict()['resource_name']: queryvalues.split(',')
                for queryparam, queryvalues in self.request.query_params.items()
                if (match := re.match(r'fields\[(?P<resource_name>\w+)\]', queryparam))
            }
        return self._sparsefields

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        qs = super().get_queryset(*args, **kwargs)
        # Since we're going to be recursing through serializers (to cover nested cases), we hand
        # the prefetching work off to the top-level serializer here. We give it:
        # - the base qs.
        # - the request, in case the serializer wants to perform any user-permission-based logic.
        # - sparsefields & includes.
        # The serializer will return a qs with all required prefetches, select_related calls and
        # annotations tacked on. If the serializer encounters any includes, it'll
        # itself pass the work down to additional serializers to get their contribution.
        return add_nested_prefetches_to_qs(
            self.get_serializer_class(),
            qs,
            request=self.request,
            sparsefields=self.get_sparsefields_as_dict(),
            includes=includes_to_dict(self.request.query_params.get('include', '').replace(',', ' ').split()),  # See https://bugs.python.org/issue28937#msg282923
        )

    def get_serializer_context(self):
        """ Pass args into the serializer's context, for field-level access. """
        context = super().get_serializer_context()
        # We don't have direct control over some serializers, so we can't always feed them their
        # specific `demanded_fields` into context how we'd like. Next best thing is to make the
        # entire sparsefields dict available for them to pick through.
        context['all_sparsefields'] = self.get_sparsefields_as_dict()
        return context


class RelatedMixin(object):
    """
    This mixin handles all related entities, whose Serializers are declared in "related_serializers"
    """

    def retrieve_related(self, request, *args, **kwargs):
        serializer_kwargs = {}
        instance = self.get_related_instance()

        if hasattr(instance, "all"):
            instance = instance.all()

        if callable(instance):
            instance = instance()

        if instance is None:
            return Response(data=None)

        if isinstance(instance, Iterable):
            serializer_kwargs["many"] = True

        serializer = self.get_related_serializer(instance, **serializer_kwargs)
        return Response(serializer.data)

    def get_related_serializer(self, instance, **kwargs):
        serializer_class = self.get_related_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(instance, **kwargs)

    def get_related_serializer_class(self):
        parent_serializer_class = self.get_serializer_class()

        if "related_field" in self.kwargs:
            field_name = self.get_related_field_name()

            # Try get the class from related_serializers
            if hasattr(parent_serializer_class, "related_serializers"):
                _class = parent_serializer_class.related_serializers.get(
                    field_name, None
                )
                if _class is None:
                    raise NotFound

            elif hasattr(parent_serializer_class, "included_serializers"):
                _class = parent_serializer_class.included_serializers.get(
                    field_name, None
                )
                if _class is None:
                    raise NotFound

            else:
                assert (
                    False
                ), 'Either "included_serializers" or "related_serializers" should be configured'

            if not isinstance(_class, type):
                return import_class_from_dotted_path(_class)
            return _class

        return parent_serializer_class

    def get_related_field_name(self):
        field_name = self.kwargs["related_field"]
        return undo_format_link_segment(field_name)

    def get_related_instance(self):
        parent_obj = self.get_object()
        parent_serializer_class = self.get_serializer_class()
        parent_serializer = parent_serializer_class(parent_obj)
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


class ModelViewSet(AutoPrefetchMixin, RelatedMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


class ReadOnlyModelViewSet(AutoPrefetchMixin, RelatedMixin, viewsets.ReadOnlyModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


class RelationshipView(generics.GenericAPIView):
    serializer_class = ResourceIdentifierObjectSerializer
    self_link_view_name = None
    related_link_view_name = None
    field_name_mapping = {}
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if getattr(self, "action", False) is None:
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
                "Could not resolve URL for hyperlinked relationship using "
                'view name "%s". You may have failed to include the related '
                "model in your API, or incorrectly configured the "
                "`lookup_field` attribute on this field."
            )
            raise ImproperlyConfigured(msg % view_name)

        if url is None:
            return None

        return Hyperlink(url, name)

    def get_links(self):
        return_data = OrderedDict()
        self_link = self.get_url(
            "self", self.self_link_view_name, self.kwargs, self.request
        )
        related_kwargs = {self.lookup_field: self.kwargs.get(self.lookup_field)}
        related_link = self.get_url(
            "related", self.related_link_view_name, related_kwargs, self.request
        )
        if self_link:
            return_data.update({"self": self_link})
        if related_link:
            return_data.update({"related": related_link})
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
        elif hasattr(instance_manager, "clear"):
            instance_manager.clear()
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
                    instance_manager=related_instance_or_manager, field="field"
                )
            # for to many
            else:
                related_instance_or_manager = self.remove_relationships(
                    instance_manager=related_instance_or_manager, field="target_field"
                )

            # have to set bulk to False since data isn't saved yet
            class_name = related_instance_or_manager.__class__.__name__
            if class_name != "ManyRelatedManager":
                related_instance_or_manager.add(*serializer.validated_data, bulk=False)
            else:
                related_instance_or_manager.add(*serializer.validated_data)
        else:
            related_model_class = related_instance_or_manager.__class__
            serializer = self.get_serializer(
                data=request.data, model_class=related_model_class
            )
            serializer.is_valid(raise_exception=True)
            setattr(
                parent_obj, self.get_related_field_name(), serializer.validated_data
            )
            parent_obj.save()
            related_instance_or_manager = (
                self.get_related_instance()
            )  # Refresh instance
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
            if frozenset(serializer.validated_data) <= frozenset(
                related_instance_or_manager.all()
            ):
                return Response(status=204)
            related_instance_or_manager.add(*serializer.validated_data)
        else:
            raise MethodNotAllowed("POST")
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
                    "This object cannot be removed from this relationship without being "
                    "added to another"
                )
        else:
            raise MethodNotAllowed("DELETE")
        result_serializer = self._instantiate_serializer(related_instance_or_manager)
        return Response(result_serializer.data)

    def get_related_instance(self):
        try:
            return getattr(self.get_object(), self.get_related_field_name())
        except AttributeError:
            raise NotFound

    def get_related_field_name(self):
        field_name = self.kwargs["related_field"]
        field_name = undo_format_link_segment(field_name)

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
        if not hasattr(self, "_resource_name"):
            instance = getattr(self.get_object(), self.get_related_field_name())
            self._resource_name = get_resource_type_from_instance(instance)
        return self._resource_name

    def set_resource_name(self, value):
        self._resource_name = value

    resource_name = property(get_resource_name, set_resource_name)
