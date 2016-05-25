from datetime import datetime
from rest_framework_json_api import serializers, relations
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
        fields = ('name', )
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
    }

    body_format = serializers.SerializerMethodField()
    # Many related from model
    comments = relations.ResourceRelatedField(
        source='comment_set', many=True, read_only=True)
    # Many related from serializer
    suggested = relations.SerializerMethodResourceRelatedField(
        source='get_suggested', model=models.Entry, many=True, read_only=True)
    # Single related from serializer
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


class ProjectSerializer(serializers.PolymorphicModelSerializer):
    polymorphic_serializers = [ArtProjectSerializer, ResearchProjectSerializer]

    class Meta:
        model = models.Project
        exclude = ('polymorphic_ctype',)


class CompanySerializer(serializers.ModelSerializer):
    current_project = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=models.Project.objects.all())
    future_projects = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=models.Project.objects.all(), many=True)

    included_serializers = {
        'current_project': ProjectSerializer,
        'future_projects': ProjectSerializer,
    }

    class Meta:
        model = models.Company
