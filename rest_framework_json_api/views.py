from django.db.models import Model, QuerySet
from django.db.models.manager import BaseManager
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, MethodNotAllowed

from rest_framework_json_api.exceptions import Conflict
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
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, BaseManager):
            related_model_class = related_instance_or_manager.model
            serializer = self.get_serializer(data=request.data, model_class=related_model_class, many=True)
            serializer.is_valid(raise_exception=True)
            related_instance_or_manager.all().delete()
            related_instance_or_manager.add(*serializer.validated_data)
        else:
            related_model_class = related_instance_or_manager.__class__
            serializer = self.get_serializer(data=request.data, model_class=related_model_class)
            serializer.is_valid(raise_exception=True)
            setattr(parent_obj, kwargs['related_field'], serializer.validated_data)
            parent_obj.save()
        result_serializer = self._instantiate_serializer(related_instance_or_manager)
        return Response(result_serializer.data)

    def post(self, request, *args, **kwargs):
        related_instance_or_manager = self.get_related_instance()

        if isinstance(related_instance_or_manager, BaseManager):
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

        if isinstance(related_instance_or_manager, BaseManager):
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
