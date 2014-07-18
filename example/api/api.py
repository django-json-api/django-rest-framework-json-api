"""
Test Serializer and Resource
"""
from django.contrib.auth import models as auth_models

from rest_framework import serializers, generics
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
    resource_name = 'data'
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
    doc
    """
    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.EmberJSONParser, )

