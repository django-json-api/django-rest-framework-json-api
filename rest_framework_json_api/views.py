from rest_framework import generics
from rest_framework.response import Response


class RelationshipView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response()

    def put(self, request, *args, **kwargs):
        return Response()

    def patch(self, request, *args, **kwargs):
        return Response()

    def post(self, request, *args, **kwargs):
        return Response()

    def delete(self, request, *args, **kwargs):
        return Response()
