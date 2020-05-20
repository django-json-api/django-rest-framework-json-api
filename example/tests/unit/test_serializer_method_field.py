from __future__ import absolute_import

import pytest
from rest_framework import serializers

from rest_framework_json_api.relations import SerializerMethodResourceRelatedField

from example.models import Blog, Entry


def test_method_name_default():
    class BlogSerializer(serializers.ModelSerializer):
        one_entry = SerializerMethodResourceRelatedField(model=Entry)

        class Meta:
            model = Blog
            fields = ['one_entry']

        def get_one_entry(self, instance):
            return Entry(id=100)

    serializer = BlogSerializer(instance=Blog())
    assert serializer.data['one_entry']['id'] == '100'


def test_method_name_custom():
    class BlogSerializer(serializers.ModelSerializer):
        one_entry = SerializerMethodResourceRelatedField(
            model=Entry,
            method_name='get_custom_entry'
        )

        class Meta:
            model = Blog
            fields = ['one_entry']

        def get_custom_entry(self, instance):
            return Entry(id=100)

    serializer = BlogSerializer(instance=Blog())
    assert serializer.data['one_entry']['id'] == '100'


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_source():
    class BlogSerializer(serializers.ModelSerializer):
        one_entry = SerializerMethodResourceRelatedField(
            model=Entry,
            source='get_custom_entry'
        )

        class Meta:
            model = Blog
            fields = ['one_entry']

        def get_custom_entry(self, instance):
            return Entry(id=100)

    serializer = BlogSerializer(instance=Blog())
    assert serializer.data['one_entry']['id'] == '100'


@pytest.mark.filterwarnings("error::DeprecationWarning")
def test_source_is_deprecated():
    with pytest.raises(DeprecationWarning):
        SerializerMethodResourceRelatedField(model=Entry, source='get_custom_entry')
