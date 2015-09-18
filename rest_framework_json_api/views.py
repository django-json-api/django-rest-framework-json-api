from rest_framework import generics
from rest_framework.response import Response
from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework.exceptions import NotFound


class RelationshipView(generics.GenericAPIView):
    serializer_class = ResourceIdentifierObjectSerializer

    def get(self, request, *args, **kwargs):
        related_instance = self.get_related_instance(kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=related_instance)
        return Response(serializer.data)

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
