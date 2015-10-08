from rest_framework import serializers
from example.models import Blog, Entry, Author, Comment


class BlogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blog
        fields = ('name', )


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ('blog', 'headline', 'body_text', 'pub_date', 'mod_date',
                'authors',)


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ('name', 'email',)


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('entry', 'body', 'author',)
