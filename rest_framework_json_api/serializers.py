import inflection
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ParseError
from rest_framework.serializers import *

from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import (
    get_resource_type_from_model, get_resource_type_from_instance,
    get_resource_type_from_serializer, get_included_serializers)


class ResourceIdentifierObjectSerializer(BaseSerializer):
    default_error_messages = {
        'incorrect_model_type': _('Incorrect model type. Expected {model_type}, received {received_type}.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    model_class = None

    def __init__(self, *args, **kwargs):
        self.model_class = kwargs.pop('model_class', self.model_class)
        if 'instance' not in kwargs and not self.model_class:
            raise RuntimeError('ResourceIdentifierObjectsSerializer must be initialized with a model class.')
        super(ResourceIdentifierObjectSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        return {
            'type': get_resource_type_from_instance(instance),
            'id': str(instance.pk)
        }

    def to_internal_value(self, data):
        if data['type'] != get_resource_type_from_model(self.model_class):
            self.fail('incorrect_model_type', model_type=self.model_class, received_type=data['type'])
        pk = data['id']
        try:
            return self.model_class.objects.get(pk=pk)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=pk)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data['pk']).__name__)


class SparseFieldsetsMixin(object):
    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        request = context.get('request') if context else None

        if request:
            sparse_fieldset_query_param = 'fields[{}]'.format(get_resource_type_from_serializer(self))
            try:
                param_name = next(key for key in request.query_params if sparse_fieldset_query_param in key)
            except StopIteration:
                pass
            else:
                fieldset = request.query_params.get(param_name).split(',')
                # iterate over a *copy* of self.fields' underlying OrderedDict, because we may modify the
                # original during the iteration. self.fields is a `rest_framework.utils.serializer_helpers.BindingDict`
                for field_name, field in self.fields.fields.copy().items():
                    if field_name == api_settings.URL_FIELD_NAME:  # leave self link there
                        continue
                    if field_name not in fieldset:
                        self.fields.pop(field_name)

        super(SparseFieldsetsMixin, self).__init__(*args, **kwargs)


class IncludedResourcesValidationMixin(object):
    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        request = context.get('request') if context else None
        view = context.get('view') if context else None

        def validate_path(serializer_class, field_path, path):
            serializers = get_included_serializers(serializer_class)
            if serializers is None:
                raise ParseError('This endpoint does not support the include parameter')
            this_field_name = inflection.underscore(field_path[0])
            this_included_serializer = serializers.get(this_field_name)
            if this_included_serializer is None:
                raise ParseError(
                    'This endpoint does not support the include parameter for path {}'.format(
                        path
                    )
                )
            if len(field_path) > 1:
                new_included_field_path = field_path[1:]
                # We go down one level in the path
                validate_path(this_included_serializer, new_included_field_path, path)

        if request and view:
            include_resources_param = request.query_params.get('include') if request else None
            if include_resources_param:
                included_resources = include_resources_param.split(',')
                for included_field_name in included_resources:
                    included_field_path = included_field_name.split('.')
                    this_serializer_class = view.get_serializer_class()
                    # lets validate the current path
                    validate_path(this_serializer_class, included_field_path, included_field_name)

        super(IncludedResourcesValidationMixin, self).__init__(*args, **kwargs)


class HyperlinkedModelSerializer(IncludedResourcesValidationMixin, SparseFieldsetsMixin, HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    Included Mixins:
    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """


class ModelSerializer(IncludedResourcesValidationMixin, SparseFieldsetsMixin, ModelSerializer):
    """
    A `ModelSerializer` is just a regular `Serializer`, except that:

    * A set of default fields are automatically populated.
    * A set of default validators are automatically populated.
    * Default `.create()` and `.update()` implementations are provided.

    The process of automatically determining a set of serializer fields
    based on the model fields is reasonably complex, but you almost certainly
    don't need to dig into the implementation.

    If the `ModelSerializer` class *doesn't* generate the set of fields that
    you need you should either declare the extra/differing fields explicitly on
    the serializer class, or simply use a `Serializer` class.


    Included Mixins:
    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """
    serializer_related_field = ResourceRelatedField

    def get_field_names(self, declared_fields, info):
        """
        We override the parent to omit explicity defined meta fields (such
        as SerializerMethodFields) from the list of declared fields
        """
        meta_fields = getattr(self.Meta, 'meta_fields', [])

        declared = OrderedDict()
        for field_name in set(declared_fields.keys()):
            field = declared_fields[field_name]
            if field_name not in meta_fields:
                declared[field_name] = field
        fields = super(ModelSerializer, self).get_field_names(declared, info)
        return list(fields) + list(getattr(self.Meta, 'meta_fields', list()))
