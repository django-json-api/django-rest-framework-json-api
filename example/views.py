from rest_framework import viewsets
from rest_framework_json_api.views import RelationshipView
from example.models import Blog, Entry, Author, Comment
from example.serializers import (
    BlogSerializer, EntrySerializer, AuthorSerializer, CommentSerializer)

from rest_framework_json_api.utils import format_drf_errors


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class BlogCustomViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer

    def handle_exception(self, exc):
        return format_drf_errors(super(BlogCustomViewSet, self).handle_exception(exc), self.get_exception_handler_context(), exc)


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    resource_name = 'posts'

    def get_serializer_class(self):
        return EntrySerializer


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


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
