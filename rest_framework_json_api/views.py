import django
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.models.manager import Manager
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, MethodNotAllowed
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework_json_api.utils import get_resource_type_from_instance, OrderedDict, Hyperlink


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
        related_link = self.get_url('related', self.related_link_view_name, related_kwargs, self.request)
        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data

    def get(self, request, *args, **kwargs):
        related_instance = self.get_related_instance()
        serializer_instance = self._instantiate_serializer(related_instance)
        return Response(serializer_instance.data)

    def patch(self, request, *args, **kwargs):
        parent_obj = self.get_object()
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, Manager):
            related_model_class = related_instance_or_manager.model
            serializer = self.get_serializer(data=request.data, model_class=related_model_class, many=True)
            serializer.is_valid(raise_exception=True)
            related_instance_or_manager.all().delete()
            # have to set bulk to False since data isn't saved yet
            if django.VERSION >= (1, 9):
                related_instance_or_manager.add(*serializer.validated_data,
                                                bulk=False)
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
            serializer = self.get_serializer(data=request.data, model_class=related_model_class, many=True)
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
            serializer = self.get_serializer(data=request.data, model_class=related_model_class, many=True)
            serializer.is_valid(raise_exception=True)
            if frozenset(serializer.validated_data).isdisjoint(frozenset(related_instance_or_manager.all())):
                return Response(status=204)
            try:
                related_instance_or_manager.remove(*serializer.validated_data)
            except AttributeError:
                raise Conflict(
                    'This object cannot be removed from this relationship without being added to another'
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
