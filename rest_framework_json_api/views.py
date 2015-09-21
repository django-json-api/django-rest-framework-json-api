from django.db.models import Model, QuerySet
from django.db.models.manager import BaseManager
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework_json_api.utils import format_relation_name, get_resource_type_from_instance


class RelationshipView(generics.GenericAPIView):
    serializer_class = ResourceIdentifierObjectSerializer

    def get(self, request, *args, **kwargs):
        related_instance = self.get_related_instance()
        serializer_instance = self._instantiate_serializer(related_instance)
        return Response(serializer_instance.data)

    def patch(self, request, *args, **kwargs):
        parent_obj = self.get_object()
        if hasattr(parent_obj, kwargs['related_field']):
            related_model_class = self.get_related_instance().__class__
            serializer = self.get_serializer(data=request.data, model_class=related_model_class)
            serializer.is_valid(raise_exception=True)
            setattr(parent_obj, kwargs['related_field'], serializer.validated_data)
            parent_obj.save()
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        return Response()

    def delete(self, request, *args, **kwargs):
        return Response()

    def get_related_instance(self):
        try:
            return getattr(self.get_object(), self.kwargs['related_field'])
        except AttributeError:
            raise NotFound

    def _instantiate_serializer(self, instance):
        if isinstance(instance, Model) or instance is None:
            return self.get_serializer(instance=instance)
        else:
            if isinstance(instance, (QuerySet, BaseManager)):
                instance = instance.all()

            return self.get_serializer(instance=instance, many=True)

    def get_resource_name(self):
        if not hasattr(self, '_resource_name'):
            instance = getattr(self.get_object(), self.kwargs['related_field'])
            self._resource_name = format_relation_name(get_resource_type_from_instance(instance))
        return self._resource_name

    def set_resource_name(self, value):
        self._resource_name = value

    resource_name = property(get_resource_name, set_resource_name)
