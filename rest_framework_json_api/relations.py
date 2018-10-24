import collections
import json
from collections import OrderedDict

import inflection
import six
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch
from django.utils.translation import ugettext_lazy as _
from rest_framework.fields import MISSING_ERROR_MESSAGE, SkipField
from rest_framework.relations import MANY_RELATION_KWARGS
from rest_framework.relations import ManyRelatedField as DRFManyRelatedField
from rest_framework.relations import PrimaryKeyRelatedField, RelatedField
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.utils import (
    Hyperlink,
    get_included_serializers,
    get_resource_type_from_instance,
    get_resource_type_from_queryset,
    get_resource_type_from_serializer
)

LINKS_PARAMS = [
    'self_link_view_name',
    'related_link_view_name',
    'related_link_lookup_field',
    'related_link_url_kwarg'
]


class SkipDataMixin(object):
    """
    This workaround skips "data" rendering for relationships
    in order to save some sql queries and improve performance
    """

    def __init__(self, *args, **kwargs):
        super(SkipDataMixin, self).__init__(*args, **kwargs)

    def get_attribute(self, instance):
        raise SkipField

    def to_representation(self, *args):
        raise NotImplementedError


class ManyRelatedFieldWithNoData(SkipDataMixin, DRFManyRelatedField):
    pass


class HyperlinkedMixin(object):
    self_link_view_name = None
    related_link_view_name = None
    related_link_lookup_field = 'pk'

    def __init__(self, self_link_view_name=None, related_link_view_name=None, **kwargs):
        if self_link_view_name is not None:
            self.self_link_view_name = self_link_view_name
        if related_link_view_name is not None:
            self.related_link_view_name = related_link_view_name

        self.related_link_lookup_field = kwargs.pop(
            'related_link_lookup_field', self.related_link_lookup_field
        )
        self.related_link_url_kwarg = kwargs.pop(
            'related_link_url_kwarg', self.related_link_lookup_field
        )

        # We include this simply for dependency injection in tests.
        # We can't add it as a class attributes or it would expect an
        # implicit `self` argument to be passed.
        self.reverse = reverse

        super(HyperlinkedMixin, self).__init__(**kwargs)

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
        self_kwargs.update({
            'related_field': self.field_name if self.field_name else self.parent.field_name
        })
        self_link = self.get_url('self', self.self_link_view_name, self_kwargs, request)

        # Assuming RelatedField will be declared in two ways:
        # 1. url(r'^authors/(?P<pk>[^/.]+)/(?P<related_field>\w+)/$',
        #         AuthorViewSet.as_view({'get': 'retrieve_related'}))
        # 2. url(r'^authors/(?P<author_pk>[^/.]+)/bio/$',
        #         AuthorBioViewSet.as_view({'get': 'retrieve'}))
        # So, if related_link_url_kwarg == 'pk' it will add 'related_field' parameter to reverse()
        if self.related_link_url_kwarg == 'pk':
            related_kwargs = self_kwargs
        else:
            related_kwargs = {self.related_link_url_kwarg: kwargs[self.related_link_lookup_field]}

        related_link = self.get_url('related', self.related_link_view_name, related_kwargs, request)

        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data


class HyperlinkedRelatedField(HyperlinkedMixin, SkipDataMixin, RelatedField):

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        This method handles creating a parent `ManyRelatedField` instance
        when the `many=True` keyword argument is passed.

        Typically you won't need to override this method.

        Note that we're over-cautious in passing most arguments to both parent
        and child classes in order to try to cover the general case. If you're
        overriding this method you'll probably want something much simpler, eg:

        .. code:: python

            @classmethod
            def many_init(cls, *args, **kwargs):
                kwargs['child'] = cls()
                return CustomManyRelatedField(*args, **kwargs)
        """
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs:
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return ManyRelatedFieldWithNoData(**list_kwargs)


class ResourceRelatedField(HyperlinkedMixin, PrimaryKeyRelatedField):
    _skip_polymorphic_optimization = True
    self_link_view_name = None
    related_link_view_name = None
    related_link_lookup_field = 'pk'

    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _(
            'Incorrect type. Expected resource identifier object, received {data_type}.'
        ),
        'incorrect_relation_type': _(
            'Incorrect relation type. Expected {relation_type}, received {received_type}.'
        ),
        'missing_type': _('Invalid resource identifier object: missing \'type\' attribute'),
        'missing_id': _('Invalid resource identifier object: missing \'id\' attribute'),
        'no_match': _('Invalid hyperlink - No URL match.'),
    }

    def __init__(self, **kwargs):
        # check for a model class that was passed in for the relation type
        model = kwargs.pop('model', None)
        if model:
            self.model = model

        super(ResourceRelatedField, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        # We need the real object to determine its type...
        return self.get_resource_type_from_included_serializer() is not None

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

    def to_internal_value(self, data):
        if isinstance(data, six.text_type):
            try:
                data = json.loads(data)
            except ValueError:
                # show a useful error if they send a `pk` instead of resource object
                self.fail('incorrect_type', data_type=type(data).__name__)
        if not isinstance(data, dict):
            self.fail('incorrect_type', data_type=type(data).__name__)

        expected_relation_type = get_resource_type_from_queryset(self.get_queryset())
        serializer_resource_type = self.get_resource_type_from_included_serializer()

        if serializer_resource_type is not None:
            expected_relation_type = serializer_resource_type

        if 'type' not in data:
            self.fail('missing_type')

        if 'id' not in data:
            self.fail('missing_id')

        if data['type'] != expected_relation_type:
            self.conflict(
                'incorrect_relation_type',
                relation_type=expected_relation_type,
                received_type=data['type']
            )

        return super(ResourceRelatedField, self).to_internal_value(data['id'])

    def to_representation(self, value):
        if getattr(self, 'pk_field', None) is not None:
            pk = self.pk_field.to_representation(value.pk)
        else:
            pk = value.pk

        resource_type = self.get_resource_type_from_included_serializer()
        if resource_type is None or not self._skip_polymorphic_optimization:
            resource_type = get_resource_type_from_instance(value)

        return OrderedDict([('type', resource_type), ('id', str(pk))])

    def get_resource_type_from_included_serializer(self):
        """
        Check to see it this resource has a different resource_name when
        included and return that name, or None
        """
        field_name = self.field_name or self.parent.field_name
        parent = self.get_parent_serializer()

        if parent is not None:
            # accept both singular and plural versions of field_name
            field_names = [
                inflection.singularize(field_name),
                inflection.pluralize(field_name)
            ]
            includes = get_included_serializers(parent)
            for field in field_names:
                if field in includes.keys():
                    return get_resource_type_from_serializer(includes[field])

        return None

    def get_parent_serializer(self):
        if hasattr(self.parent, 'parent') and self.is_serializer(self.parent.parent):
            return self.parent.parent
        elif self.is_serializer(self.parent):
            return self.parent

        return None

    def is_serializer(self, candidate):
        return isinstance(candidate, Serializer)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                json.dumps(self.to_representation(item)),
                self.display_value(item)
            )
            for item in queryset
        ])


class PolymorphicResourceRelatedField(ResourceRelatedField):
    """
    Inform DRF that the relation must be considered polymorphic.
    Takes a `polymorphic_serializer` as the first positional argument to
    retrieve then validate the accepted types set.
    """

    _skip_polymorphic_optimization = False
    default_error_messages = dict(ResourceRelatedField.default_error_messages, **{
        'incorrect_relation_type': _('Incorrect relation type. Expected one of [{relation_type}], '
                                     'received {received_type}.'),
    })

    def __init__(self, polymorphic_serializer, *args, **kwargs):
        self.polymorphic_serializer = polymorphic_serializer
        super(PolymorphicResourceRelatedField, self).__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if isinstance(data, six.text_type):
            try:
                data = json.loads(data)
            except ValueError:
                # show a useful error if they send a `pk` instead of resource object
                self.fail('incorrect_type', data_type=type(data).__name__)
        if not isinstance(data, dict):
            self.fail('incorrect_type', data_type=type(data).__name__)

        if 'type' not in data:
            self.fail('missing_type')

        if 'id' not in data:
            self.fail('missing_id')

        expected_relation_types = self.polymorphic_serializer.get_polymorphic_types()

        if data['type'] not in expected_relation_types:
            self.conflict('incorrect_relation_type', relation_type=", ".join(
                expected_relation_types), received_type=data['type'])

        return super(ResourceRelatedField, self).to_internal_value(data['id'])


class SerializerMethodResourceRelatedField(ResourceRelatedField):
    """
    Allows us to use serializer method RelatedFields
    with return querysets
    """
    def __new__(cls, *args, **kwargs):
        """
        We override this because getting serializer methods
        fails at the base class when many=True
        """
        if kwargs.pop('many', False):
            return cls.many_init(*args, **kwargs)
        return super(ResourceRelatedField, cls).__new__(cls, *args, **kwargs)

    def __init__(self, child_relation=None, *args, **kwargs):
        model = kwargs.pop('model', None)
        if child_relation is not None:
            self.child_relation = child_relation
        if model:
            self.model = model
        super(SerializerMethodResourceRelatedField, self).__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {k: kwargs.pop(k) for k in LINKS_PARAMS if k in kwargs}
        list_kwargs['child_relation'] = cls(*args, **kwargs)
        for key in kwargs.keys():
            if key in ('model',) + MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return cls(**list_kwargs)

    def get_attribute(self, instance):
        # check for a source fn defined on the serializer instead of the model
        if self.source and hasattr(self.parent, self.source):
            serializer_method = getattr(self.parent, self.source)
            if hasattr(serializer_method, '__call__'):
                return serializer_method(instance)
        return super(SerializerMethodResourceRelatedField, self).get_attribute(instance)

    def to_representation(self, value):
        if isinstance(value, collections.Iterable):
            base = super(SerializerMethodResourceRelatedField, self)
            return [base.to_representation(x) for x in value]
        return super(SerializerMethodResourceRelatedField, self).to_representation(value)


class SerializerMethodHyperlinkedRelatedField(SkipDataMixin, SerializerMethodResourceRelatedField):
    pass
