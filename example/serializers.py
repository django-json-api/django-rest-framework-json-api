from rest_framework import serializers


class BlogSerializer(serializers.Serializer):

    class Meta:
        fields = ('name', )
