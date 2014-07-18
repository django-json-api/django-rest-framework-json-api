"""
Test Serializer and Resource
"""
from django.contrib.auth import models as auth_models

from rest_framework import serializers, generics, viewsets
from rest_framework.response import Response

from rest_framework_ember import renderers, parsers


class IdentitySerializer(serializers.ModelSerializer):
    """
    Identity Serializer
    """
    class Meta:
        model = auth_models.User
        fields = (
            'id', 'first_name', 'last_name', 'email', )


class User(generics.GenericAPIView):
    """
    Current user's identity endpoint.

    GET /me
    """
    serializer_class = IdentitySerializer
    allowed_methods = ['GET']

    def get_queryset(self):
        return auth_models.User.objects.all()

    def get(self, request, pk=None):
        """
        GET request
        """
        obj = self.get_object()
        serializer = self.serializer_class(obj)
        return Response(serializer.data)


class UserEmber(User):
    """
    Use the rest_framework_ember Renderer/Parser
    """
    resource_name = 'data'

    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.EmberJSONParser, )


class EmberUserModelViewSet(viewsets.ModelViewSet):
    model = auth_models.User
    serializer_class = IdentitySerializer
    allowed_methods = ['GET', 'POST', 'PUT', ]
    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.EmberJSONParser, )


