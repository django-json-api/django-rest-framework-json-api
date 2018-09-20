import inflection
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ParseError
from rest_framework.serializers import *  # noqa: F403

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import (
    get_included_resources,
    get_included_serializers,
    get_resource_type_from_instance,
    get_resource_type_from_model,
    get_resource_type_from_serializer
)


class ResourceIdentifierObjectSerializer(BaseSerializer):
    default_error_messages = {
        'incorrect_model_type': _(
            'Incorrect model type. Expected {model_type}, received {received_type}.'
        ),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    model_class = None

    def __init__(self, *args, **kwargs):
        self.model_class = kwargs.pop('model_class', self.model_class)
        if 'instance' not in kwargs and not self.model_class:
            raise RuntimeError(
                'ResourceIdentifierObjectsSerializer must be initialized with a model class.'
            )
        super(ResourceIdentifierObjectSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        return {
            'type': get_resource_type_from_instance(instance),
            'id': str(instance.pk)
        }

    def to_internal_value(self, data):
        if data['type'] != get_resource_type_from_model(self.model_class):
            self.fail(
                'incorrect_model_type', model_type=self.model_class, received_type=data['type']
            )
        pk = data['id']
        try:
            return self.model_class.objects.get(pk=pk)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=pk)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data['pk']).__name__)


class SparseFieldsetsMixin(object):
    def __init__(self, *args, **kwargs):
        super(SparseFieldsetsMixin, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        request = context.get('request') if context else None

        if request:
            sparse_fieldset_query_param = 'fields[{}]'.format(
                get_resource_type_from_serializer(self)
            )
            try:
                param_name = next(
                    key for key in request.query_params if sparse_fieldset_query_param in key
                )
            except StopIteration:
                pass
            else:
                fieldset = request.query_params.get(param_name).split(',')
                # iterate over a *copy* of self.fields' underlying OrderedDict, because we may
                # modify the original during the iteration.
                # self.fields is a `rest_framework.utils.serializer_helpers.BindingDict`
                for field_name, field in self.fields.fields.copy().items():
                    if field_name == api_settings.URL_FIELD_NAME:  # leave self link there
                        continue
                    if field_name not in fieldset:
                        self.fields.pop(field_name)


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
            included_resources = get_included_resources(request)
            for included_field_name in included_resources:
                included_field_path = included_field_name.split('.')
                this_serializer_class = view.get_serializer_class()
                # lets validate the current path
                validate_path(this_serializer_class, included_field_path, included_field_name)

        super(IncludedResourcesValidationMixin, self).__init__(*args, **kwargs)


class HyperlinkedModelSerializer(
        IncludedResourcesValidationMixin, SparseFieldsetsMixin, HyperlinkedModelSerializer
):
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

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        readable_fields = [
            field for field in self.fields.values()
            if not field.write_only
        ]

        for field in readable_fields:
            try:
                field_representation = self._get_field_representation(field, instance)
                ret[field.field_name] = field_representation
            except SkipField:
                continue

        return ret

    def _get_field_representation(self, field, instance):
        request = self.context.get('request')
        is_included = field.source in get_included_resources(request)
        if not is_included and \
                isinstance(field, ModelSerializer) and \
                hasattr(instance, field.source + '_id'):
            attribute = getattr(instance, field.source + '_id')

            if attribute is None:
                return None

            resource_type = get_resource_type_from_serializer(field)
            if resource_type:
                return OrderedDict([('type', resource_type), ('id', attribute)])

        attribute = field.get_attribute(instance)

        # We skip `to_representation` for `None` values so that fields do
        # not have to explicitly deal with that case.
        #
        # For related fields with `use_pk_only_optimization` we need to
        # resolve the pk value.
        check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
        if check_for_none is None:
            return None
        else:
            return field.to_representation(attribute)


class PolymorphicSerializerMetaclass(SerializerMetaclass):
    """
    This metaclass ensures that the `polymorphic_serializers` is correctly defined on a
    `PolymorphicSerializer` class and make a cache of model/serializer/type mappings.
    """

    def __new__(cls, name, bases, attrs):
        new_class = super(PolymorphicSerializerMetaclass, cls).__new__(cls, name, bases, attrs)

        # Ensure initialization is only performed for subclasses of PolymorphicModelSerializer
        # (excluding PolymorphicModelSerializer class itself).
        parents = [b for b in bases if isinstance(b, PolymorphicSerializerMetaclass)]
        if not parents:
            return new_class

        polymorphic_serializers = getattr(new_class, 'polymorphic_serializers', None)
        if not polymorphic_serializers:
            raise NotImplementedError(
                "A PolymorphicModelSerializer must define a `polymorphic_serializers` attribute.")
        serializer_to_model = {
            serializer: serializer.Meta.model for serializer in polymorphic_serializers}
        model_to_serializer = {
            serializer.Meta.model: serializer for serializer in polymorphic_serializers}
        type_to_serializer = {
            get_resource_type_from_serializer(serializer): serializer for
            serializer in polymorphic_serializers}
        new_class._poly_serializer_model_map = serializer_to_model
        new_class._poly_model_serializer_map = model_to_serializer
        new_class._poly_type_serializer_map = type_to_serializer
        new_class._poly_force_type_resolution = True

        # Flag each linked polymorphic serializer to force type resolution based on instance
        for serializer in polymorphic_serializers:
            serializer._poly_force_type_resolution = True

        return new_class


@six.add_metaclass(PolymorphicSerializerMetaclass)
class PolymorphicModelSerializer(ModelSerializer):
    """
    A serializer for polymorphic models.
    Useful for "lazy" parent models. Leaves should be represented with a regular serializer.
    """
    def get_fields(self):
        """
        Return an exhaustive list of the polymorphic serializer fields.
        """
        if self.instance not in (None, []):
            if not isinstance(self.instance, QuerySet):
                serializer_class = self.get_polymorphic_serializer_for_instance(self.instance)
                return serializer_class(self.instance, context=self.context).get_fields()
            else:
                raise Exception("Cannot get fields from a polymorphic serializer given a queryset")
        return super(PolymorphicModelSerializer, self).get_fields()

    @classmethod
    def get_polymorphic_serializer_for_instance(cls, instance):
        """
        Return the polymorphic serializer associated with the given instance/model.
        Raise `NotImplementedError` if no serializer is found for the given model. This usually
        means that a serializer is missing in the class's `polymorphic_serializers` attribute.
        """
        try:
            return cls._poly_model_serializer_map[instance._meta.model]
        except KeyError:
            raise NotImplementedError(
                "No polymorphic serializer has been found for model {}".format(
                    instance._meta.model.__name__))

    @classmethod
    def get_polymorphic_model_for_serializer(cls, serializer):
        """
        Return the polymorphic model associated with the given serializer.
        Raise `NotImplementedError` if no model is found for the given serializer. This usually
        means that a serializer is missing in the class's `polymorphic_serializers` attribute.
        """
        try:
            return cls._poly_serializer_model_map[serializer]
        except KeyError:
            raise NotImplementedError(
                "No polymorphic model has been found for serializer {}".format(serializer.__name__))

    @classmethod
    def get_polymorphic_serializer_for_type(cls, obj_type):
        """
        Return the polymorphic serializer associated with the given type.
        Raise `NotImplementedError` if no serializer is found for the given type. This usually
        means that a serializer is missing in the class's `polymorphic_serializers` attribute.
        """
        try:
            return cls._poly_type_serializer_map[obj_type]
        except KeyError:
            raise NotImplementedError(
                "No polymorphic serializer has been found for type {}".format(obj_type))

    @classmethod
    def get_polymorphic_model_for_type(cls, obj_type):
        """
        Return the polymorphic model associated with the given type.
        Raise `NotImplementedError` if no model is found for the given type. This usually
        means that a serializer is missing in the class's `polymorphic_serializers` attribute.
        """
        return cls.get_polymorphic_model_for_serializer(
            cls.get_polymorphic_serializer_for_type(obj_type))

    @classmethod
    def get_polymorphic_types(cls):
        """
        Return the list of accepted types.
        """
        return cls._poly_type_serializer_map.keys()

    def to_representation(self, instance):
        """
        Retrieve the appropriate polymorphic serializer and use this to handle representation.
        """
        serializer_class = self.get_polymorphic_serializer_for_instance(instance)
        return serializer_class(instance, context=self.context).to_representation(instance)

    def to_internal_value(self, data):
        """
        Ensure that the given type is one of the expected polymorphic types, then retrieve the
        appropriate polymorphic serializer and use this to handle internal value.
        """
        received_type = data.get('type')
        expected_types = self.get_polymorphic_types()
        if received_type not in expected_types:
            raise Conflict(
                'Incorrect relation type. Expected on of [{expected_types}], '
                'received {received_type}.'.format(
                    expected_types=', '.join(expected_types), received_type=received_type))
        serializer_class = self.get_polymorphic_serializer_for_type(received_type)
        self.__class__ = serializer_class
        return serializer_class(data, context=self.context).to_internal_value(data)
