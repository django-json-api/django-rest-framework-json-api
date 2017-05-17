from django.contrib.auth import models as auth_models
from rest_framework import serializers


class IdentitySerializer(serializers.ModelSerializer):
    """
    Identity Serializer
    """

    def validate_first_name(self, data):
        if len(data) > 10:
            raise serializers.ValidationError(
                'There\'s a problem with first name')
        return data

    def validate_last_name(self, data):
        if len(data) > 10:
            raise serializers.ValidationError(
                {
                    'id': 'armageddon101',
                    'detail': 'Hey! You need a last name!',
                    'meta': 'something',
                }
            )
        return data

    class Meta:
        model = auth_models.User
        fields = (
            'id', 'first_name', 'last_name', 'email', )
