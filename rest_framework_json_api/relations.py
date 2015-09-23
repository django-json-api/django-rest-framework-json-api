from rest_framework.exceptions import ValidationError
from rest_framework.fields import MISSING_ERROR_MESSAGE
from rest_framework.relations import *
from django.utils.translation import ugettext_lazy as _

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.utils import format_relation_name, Hyperlink, \
    get_resource_type_from_queryset, get_resource_type_from_instance


class HyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    This field exists for the sole purpose of accepting PKs as well as URLs
    when data is submitted back to the serializer
    """
    default_error_messages = {
        'required': _('This field is required.'),
        'no_match': _('Invalid hyperlink - No URL match.'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match.'),
        'does_not_exist': _('Invalid hyperlink - Object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected URL string, received {data_type}.'),
        'pk_does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_pk_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            # Try parsing links first for the browseable API
            return super(HyperlinkedRelatedField, self).to_internal_value(data)
        except ValidationError:
            if self.pk_field is not None:
                data = self.pk_field.to_internal_value(data)
            try:
                return self.get_queryset().get(pk=data)
            except ObjectDoesNotExist:
                self.fail('pk_does_not_exist', pk_value=data)
            except (TypeError, ValueError):
                self.fail('incorrect_pk_type', data_type=type(data).__name__)


class ResourceRelatedField(PrimaryKeyRelatedField):
    self_link_view_name = None
    related_link_view_name = None
    related_link_lookup_field = 'pk'

    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected resource identifier object, received {data_type}.'),
        'incorrect_relation_type': _('Incorrect relation type. Expected {relation_type}, received {received_type}.'),
        'no_match': _('Invalid hyperlink - No URL match.'),
    }

    def __init__(self, self_link_view_name=None, related_link_view_name=None, **kwargs):
        if self_link_view_name is not None:
            self.self_link_view_name = self_link_view_name
        if related_link_view_name is not None:
            self.related_link_view_name = related_link_view_name

        self.related_link_lookup_field = kwargs.pop('related_link_lookup_field', self.related_link_lookup_field)
        self.related_link_url_kwarg = kwargs.pop('related_link_url_kwarg', self.related_link_lookup_field)

        # We include this simply for dependency injection in tests.
        # We can't add it as a class attributes or it would expect an
        # implicit `self` argument to be passed.
        self.reverse = reverse

        super(ResourceRelatedField, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        # We need the real object to determine its type...
        return False

    def conflict(self, key, **kwargs):
        """
        A helper method that simply raises a validation error.
        """
        try:
            msg = self.error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)
        message_string = msg.format(**kwargs)
        raise Conflict(message_string)

    def get_url(self, name, view_name, kwargs, request):
        """
        Given a name, view name and kwargs, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """

        # Return None if the view name is not supplied
        if not view_name:
            return None

        # Return the hyperlink, or error if incorrectly configured.
        try:
            url = self.reverse(view_name, kwargs=kwargs, request=request)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s".'
            )
            raise ImproperlyConfigured(msg % view_name)

        if url is None:
            return None

        return Hyperlink(url, name)

    def get_links(self, obj=None, lookup_field='pk'):
        request = self.context.get('request', None)
        view = self.context.get('view', None)
        return_data = OrderedDict()

        kwargs = {lookup_field: getattr(obj, lookup_field) if obj else view.kwargs[lookup_field]}

        self_kwargs = kwargs.copy()
        self_kwargs.update({'related_field': self.field_name if self.field_name else self.parent.field_name})
        self_link = self.get_url('self', self.self_link_view_name, self_kwargs, request)

        related_kwargs = {self.related_link_url_kwarg: kwargs[self.related_link_lookup_field]}
        related_link = self.get_url('related', self.related_link_view_name, related_kwargs, request)

        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data

    def to_internal_value(self, data):
        expected_relation_type = get_resource_type_from_queryset(self.queryset)
        if not isinstance(data, dict):
            self.fail('incorrect_type', data_type=type(data).__name__)
        if data['type'] != expected_relation_type:
            self.conflict('incorrect_relation_type', relation_type=expected_relation_type, received_type=data['type'])
        return super(ResourceRelatedField, self).to_internal_value(data['id'])

    def to_representation(self, value):
        if getattr(self, 'pk_field', None) is not None:
            pk = self.pk_field.to_representation(value.pk)
        else:
            pk = value.pk

        return OrderedDict([('type', format_relation_name(get_resource_type_from_instance(value))), ('id', str(pk))])

