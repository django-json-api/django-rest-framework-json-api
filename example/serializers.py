from datetime import datetime
from django.db.models.query import QuerySet
from rest_framework.utils.serializer_helpers import BindingDict
from rest_framework_json_api import serializers, relations, utils
from example import models


class BlogSerializer(serializers.ModelSerializer):

    copyright = serializers.SerializerMethodField()

    def get_copyright(self, resource):
        return datetime.now().year

    def get_root_meta(self, resource, many):
        return {
            'api_docs': '/docs/api/blogs'
        }

    class Meta:
        model = models.Blog
        fields = ('name', 'url',)
        meta_fields = ('copyright',)


class EntrySerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # to make testing more concise we'll only output the
        # `featured` field when it's requested via `include`
        request = kwargs.get('context', {}).get('request')
        if request and 'featured' not in request.query_params.get('include', []):
            self.fields.pop('featured')
        super(EntrySerializer, self).__init__(*args, **kwargs)

    included_serializers = {
        'authors': 'example.serializers.AuthorSerializer',
        'comments': 'example.serializers.CommentSerializer',
        'featured': 'example.serializers.EntrySerializer',
        'suggested': 'example.serializers.EntrySerializer',
    }

    body_format = serializers.SerializerMethodField()
    # many related from model
    comments = relations.ResourceRelatedField(
            source='comment_set', many=True, read_only=True)
    # many related from serializer
    suggested = relations.SerializerMethodResourceRelatedField(
            source='get_suggested', model=models.Entry, many=True, read_only=True)
    # single related from serializer
    featured = relations.SerializerMethodResourceRelatedField(
            source='get_featured', model=models.Entry, read_only=True)

    def get_suggested(self, obj):
        return models.Entry.objects.exclude(pk=obj.pk)

    def get_featured(self, obj):
        return models.Entry.objects.exclude(pk=obj.pk).first()

    def get_body_format(self, obj):
        return 'text'

    class Meta:
        model = models.Entry
        fields = ('blog', 'headline', 'body_text', 'pub_date', 'mod_date',
                  'authors', 'comments', 'featured', 'suggested',)
        meta_fields = ('body_format',)


class AuthorBioSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AuthorBio
        fields = ('author', 'body',)


class AuthorSerializer(serializers.ModelSerializer):
    included_serializers = {
        'bio': AuthorBioSerializer
    }

    class Meta:
        model = models.Author
        fields = ('name', 'email', 'bio')


class CommentSerializer(serializers.ModelSerializer):
    included_serializers = {
        'entry': EntrySerializer,
        'author': AuthorSerializer
    }

    class Meta:
        model = models.Comment
        exclude = ('created_at', 'modified_at',)
        # fields = ('entry', 'body', 'author',)


class ArtProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArtProject
        exclude = ('polymorphic_ctype',)


class ResearchProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResearchProject
        exclude = ('polymorphic_ctype',)


class ProjectSerializer(serializers.ModelSerializer):

    polymorphic_serializers = [
        {'model': models.ArtProject, 'serializer': ArtProjectSerializer},
        {'model': models.ResearchProject, 'serializer': ResearchProjectSerializer},
    ]

    class Meta:
        model = models.Project
        exclude = ('polymorphic_ctype',)

    def _get_actual_serializer_from_instance(self, instance):
        for info in self.polymorphic_serializers:
            if isinstance(instance, info.get('model')):
                actual_serializer = info.get('serializer')
                return actual_serializer(instance, context=self.context)

    @property
    def fields(self):
        _fields = BindingDict(self)
        for key, value in self.get_fields().items():
            _fields[key] = value
        return _fields

    def get_fields(self):
        if self.instance is not None:
            if not isinstance(self.instance, QuerySet):
                return self._get_actual_serializer_from_instance(self.instance).get_fields()
            else:
                raise Exception("Cannot get fields from a polymorphic serializer given a queryset")
        return super(ProjectSerializer, self).get_fields()

    def to_representation(self, instance):
        # Handle polymorphism
        return self._get_actual_serializer_from_instance(instance).to_representation(instance)

    def to_internal_value(self, data):
        data_type = data.get('type')
        for info in self.polymorphic_serializers:
            actual_serializer = info['serializer']
            if data_type == utils.get_resource_type_from_serializer(actual_serializer):
                self.__class__ = actual_serializer
                return actual_serializer(data, context=self.context).to_internal_value(data)
        raise Exception("Could not deserialize")


class CompanySerializer(serializers.ModelSerializer):
    included_serializers = {
        'current_project': ProjectSerializer,
        'future_projects': ProjectSerializer,
    }

    class Meta:
        model = models.Company
