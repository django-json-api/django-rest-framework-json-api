from rest_framework import viewsets
from rest_framework_json_api.views import RelationshipView
from example.models import Blog, Entry, Author, Comment, RenamedAuthor
from example.serializers import (
        BlogSerializer, EntrySerializer, AuthorSerializer, CommentSerializer,
        RenamedAuthorSerializer)


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    resource_name = 'posts'


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class RenamedAuthorViewSet(viewsets.ModelViewSet):
    queryset = RenamedAuthor.objects.all()
    serializer_class = RenamedAuthorSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class EntryRelationshipView(RelationshipView):
    queryset = Entry.objects.all()


class BlogRelationshipView(RelationshipView):
    queryset = Blog.objects.all()


class CommentRelationshipView(RelationshipView):
    queryset = Comment.objects.all()


class AuthorRelationshipView(RelationshipView):
    queryset = Author.objects.all()
    self_link_view_name = 'author-relationships'
