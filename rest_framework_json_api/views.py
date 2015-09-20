from django.db.models import Model, QuerySet
from django.db.models.manager import BaseManager
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework.exceptions import NotFound


class RelationshipView(generics.GenericAPIView):
    serializer_class = ResourceIdentifierObjectSerializer
    renderer_classes = (JSONRenderer, )

    def get(self, request, *args, **kwargs):
        related_instance = self.get_related_instance(kwargs)
        serializer_instance = self.instantiate_serializer(related_instance)
        return Response(serializer_instance.data)

    def put(self, request, *args, **kwargs):
        return Response()

    def patch(self, request, *args, **kwargs):
        return Response()

    def post(self, request, *args, **kwargs):
        return Response()

    def delete(self, request, *args, **kwargs):
        return Response()

    def get_related_instance(self, kwargs):
        try:
            return getattr(self.get_object(), kwargs['related_field'])
        except AttributeError:
            raise NotFound

    def instantiate_serializer(self, instance):
        serializer_class = self.get_serializer_class()
        if isinstance(instance, Model):
            return serializer_class(instance=instance)
        else:
            if isinstance(instance, (QuerySet, BaseManager)):
                instance = instance.all()

            return serializer_class(instance=instance, many=True)


