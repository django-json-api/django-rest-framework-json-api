from rest_framework_json_api import serializers, relations
from example.models import Blog, Entry, Author, AuthorBio, Comment


class BlogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blog
        fields = ('name', )


class EntrySerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # to make testing more concise we'll only output the
        # `suggested` field when it's requested via `include`
        request = kwargs.get('context', {}).get('request')
        if request and 'suggested' not in request.query_params.get('include', []):
            self.fields.pop('suggested')
        super(EntrySerializer, self).__init__(*args, **kwargs)

    included_serializers = {
        'comments': 'example.serializers.CommentSerializer',
        'suggested': 'example.serializers.EntrySerializer',
    }

    comments = relations.ResourceRelatedField(
            source='comment_set', many=True, read_only=True)
    suggested = relations.SerializerMethodResourceRelatedField(
            source='get_suggested', model=Entry, read_only=True)

    def get_suggested(self, obj):
        return Entry.objects.exclude(pk=obj.pk).first()

    class Meta:
        model = Entry
        fields = ('blog', 'headline', 'body_text', 'pub_date', 'mod_date',
                'authors', 'comments', 'suggested',)


class AuthorBioSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthorBio
        fields = ('author', 'body',)


class AuthorSerializer(serializers.ModelSerializer):
    included_serializers = {
        'bio': AuthorBioSerializer
    }

    class Meta:
        model = Author
        fields = ('name', 'email', 'bio')


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('entry', 'body', 'author',)
