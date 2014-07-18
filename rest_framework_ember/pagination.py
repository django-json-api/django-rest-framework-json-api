from rest_framework import serializers
from rest_framework import pagination
from rest_framework.templatetags.rest_framework import replace_query_param

from rest_framework.resource_name import get_resource_name


class NextPageLinkField(serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class NextPageField(serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.has_next():
            return None
        return value.next_page_number()


class PreviousPageLinkField(serializers.Field):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class PreviousPageField(serializers.Field):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_native(self, value):
        if not value.has_previous():
            return None
        return value.previous_page_number()


class EmberPaginationSerializer(pagination.BasePaginationSerializer):
    next = NextPageField(source='*')
    next_link = NextPageLinkField(source='*')
    previous = PreviousPageField(source='*')
    previous_link = PreviousPageField(source='*')
    count = serializers.Field(source='paginator.count')

    def __init__(self, *args, **kwargs):
        super(pagination.BasePaginationSerializer, self).__init__(
                *args, **kwargs)

        # get the dynamic root key
        results_field = get_resource_name(
            kwargs.get('context').get('view'))
        object_serializer = self.opts.object_serializer_class

        if 'context' in kwargs:
            context_kwarg = {'context': kwargs['context']}
        else:
            context_kwarg = {}

        self.fields[results_field] = object_serializer(source='object_list', **context_kwarg)
