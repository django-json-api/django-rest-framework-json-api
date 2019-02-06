"""
Renderers
"""
import copy
from collections import Iterable, OrderedDict, defaultdict

import inflection
from django.db.models import Manager
from django.utils import encoding, six
from rest_framework import relations, renderers
from rest_framework.serializers import BaseSerializer, ListSerializer, Serializer
from rest_framework.settings import api_settings

import rest_framework_json_api
from rest_framework_json_api import utils
from rest_framework_json_api.relations import HyperlinkedMixin, ResourceRelatedField, SkipDataMixin


class JSONRenderer(renderers.JSONRenderer):
    """
    The `JSONRenderer` exposes a number of methods that you may override if you need highly
    custom rendering control.

    Render a JSON response per the JSON API spec:

    .. code:: json

        {
            "data": [{
                "type": "companies",
                "id": 1,
                "attributes": {
                    "name": "Mozilla",
                    "slug": "mozilla",
                    "date-created": "2014-03-13 16:33:37"
                }
            }, {
                "type": "companies",
                "id": 2,
                ...
            }]
        }

    """

    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'

    @classmethod
    def extract_attributes(cls, fields, resource):
        """
        Builds the `attributes` object of the JSON API resource object.
        """
        data = OrderedDict()
        for field_name, field in six.iteritems(fields):
            # ID is always provided in the root of JSON API so remove it from attributes
            if field_name == 'id':
                continue
            # don't output a key for write only fields
            if fields[field_name].write_only:
                continue
            # Skip fields with relations
            if isinstance(
                    field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)
            ):
                continue

            # Skip read_only attribute fields when `resource` is an empty
            # serializer. Prevents the "Raw Data" form of the browsable API
            # from rendering `"foo": null` for read only fields
            try:
                resource[field_name]
            except KeyError:
                if fields[field_name].read_only:
                    continue

            data.update({
                field_name: resource.get(field_name)
            })

        return utils._format_object(data)

    @classmethod
    def extract_relationships(cls, fields, resource, resource_instance):
        """
        Builds the relationships top level object based on related serializers.
        """
        # Avoid circular deps
        from rest_framework_json_api.relations import ResourceRelatedField

        data = OrderedDict()

        # Don't try to extract relationships from a non-existent resource
        if resource_instance is None:
            return

        for field_name, field in six.iteritems(fields):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # don't output a key for write only fields
            if fields[field_name].write_only:
                continue

            # Skip fields without relations
            if not isinstance(
                field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)
            ):
                continue

            source = field.source
            relation_type = utils.get_related_resource_type(field)

            if isinstance(field, relations.HyperlinkedIdentityField):
                resolved, relation_instance = utils.get_relation_instance(
                    resource_instance, source, field.parent
                )
                if not resolved:
                    continue
                # special case for HyperlinkedIdentityField
                relation_data = list()

                # Don't try to query an empty relation
                relation_queryset = relation_instance \
                    if relation_instance is not None else list()

                for related_object in relation_queryset:
                    relation_data.append(
                        OrderedDict([
                            ('type', relation_type),
                            ('id', encoding.force_text(related_object.pk))
                        ])
                    )

                data.update({field_name: {
                    'links': {
                        "related": resource.get(field_name)},
                    'data': relation_data,
                    'meta': {
                        'count': len(relation_data)
                    }
                }})
                continue

            relation_data = {}
            if isinstance(field, HyperlinkedMixin):
                field_links = field.get_links(resource_instance, field.related_link_lookup_field)
                relation_data.update({'links': field_links} if field_links else dict())
                data.update({field_name: relation_data})

            if isinstance(field, (ResourceRelatedField, )):
                if not isinstance(field, SkipDataMixin):
                    relation_data.update({'data': resource.get(field_name)})

                data.update({field_name: relation_data})
                continue

            if isinstance(
                    field, (relations.PrimaryKeyRelatedField, relations.HyperlinkedRelatedField)
            ):
                resolved, relation = utils.get_relation_instance(
                    resource_instance, '%s_id' % source, field.parent
                )
                if not resolved:
                    continue
                relation_id = relation if resource.get(field_name) else None
                relation_data = {
                    'data': (
                        OrderedDict([
                            ('type', relation_type), ('id', encoding.force_text(relation_id))
                        ])
                        if relation_id is not None else None)
                }

                if (
                    isinstance(field, relations.HyperlinkedRelatedField) and
                    resource.get(field_name)
                ):
                    relation_data.update(
                        {
                            'links': {
                                'related': resource.get(field_name)
                            }
                        }
                    )
                data.update({field_name: relation_data})
                continue

            if isinstance(field, relations.ManyRelatedField):
                resolved, relation_instance = utils.get_relation_instance(
                    resource_instance, source, field.parent
                )
                if not resolved:
                    continue

                relation_data = {}

                if isinstance(resource.get(field_name), Iterable):
                    relation_data.update(
                        {
                            'meta': {'count': len(resource.get(field_name))}
                        }
                    )

                if isinstance(field.child_relation, ResourceRelatedField):
                    # special case for ResourceRelatedField
                    relation_data.update(
                        {'data': resource.get(field_name)}
                    )

                if isinstance(field.child_relation, HyperlinkedMixin):
                    field_links = field.child_relation.get_links(
                        resource_instance,
                        field.child_relation.related_link_lookup_field
                    )
                    relation_data.update(
                        {'links': field_links}
                        if field_links else dict()
                    )

                    data.update({field_name: relation_data})
                    continue

                relation_data = list()
                for nested_resource_instance in relation_instance:
                    nested_resource_instance_type = (
                        relation_type or
                        utils.get_resource_type_from_instance(nested_resource_instance)
                    )

                    relation_data.append(OrderedDict([
                        ('type', nested_resource_instance_type),
                        ('id', encoding.force_text(nested_resource_instance.pk))
                    ]))
                data.update({
                    field_name: {
                        'data': relation_data,
                        'meta': {
                            'count': len(relation_data)
                        }
                    }
                })
                continue

            if isinstance(field, ListSerializer):
                resolved, relation_instance = utils.get_relation_instance(
                    resource_instance, source, field.parent
                )
                if not resolved:
                    continue

                relation_data = list()

                serializer_data = resource.get(field_name)
                resource_instance_queryset = list(relation_instance)
                if isinstance(serializer_data, list):
                    for position in range(len(serializer_data)):
                        nested_resource_instance = resource_instance_queryset[position]
                        nested_resource_instance_type = (
                            relation_type or
                            utils.get_resource_type_from_instance(nested_resource_instance)
                        )

                        relation_data.append(OrderedDict([
                            ('type', nested_resource_instance_type),
                            ('id', encoding.force_text(nested_resource_instance.pk))
                        ]))

                    data.update({field_name: {'data': relation_data}})
                    continue

            if isinstance(field, Serializer):
                relation_instance_id = getattr(resource_instance, source + "_id", None)
                if not relation_instance_id:
                    resolved, relation_instance = utils.get_relation_instance(
                        resource_instance, source, field.parent
                    )
                    if not resolved:
                        continue

                    if relation_instance is not None:
                        relation_instance_id = relation_instance.pk

                data.update({
                    field_name: {
                        'data': (
                            OrderedDict([
                                ('type', relation_type),
                                ('id', encoding.force_text(relation_instance_id))
                            ]) if resource.get(field_name) else None)
                    }
                })
                continue

        return utils._format_object(data)

    @classmethod
    def extract_relation_instance(cls, field_name, field, resource_instance, serializer):
        """
        Determines what instance represents given relation and extracts it.

        Relation instance is determined by given field_name or source configured on
        field. As fallback is a serializer method called with name of field's source.
        """
        relation_instance = None

        try:
            relation_instance = getattr(resource_instance, field_name)
        except AttributeError:
            try:
                # For ManyRelatedFields if `related_name` is not set
                # we need to access `foo_set` from `source`
                relation_instance = getattr(resource_instance, field.child_relation.source)
            except AttributeError:
                if hasattr(serializer, field.source):
                    serializer_method = getattr(serializer, field.source)
                    relation_instance = serializer_method(resource_instance)
                else:
                    # case when source is a simple remap on resource_instance
                    try:
                        relation_instance = getattr(resource_instance, field.source)
                    except AttributeError:
                        pass

        return relation_instance

    @classmethod
    def extract_included(cls, fields, resource, resource_instance, included_resources,
                         included_cache):
        """
        Adds related data to the top level included key when the request includes
        ?include=example,example_field2
        """
        # this function may be called with an empty record (example: Browsable Interface)
        if not resource_instance:
            return

        current_serializer = fields.serializer
        context = current_serializer.context
        included_serializers = utils.get_included_serializers(current_serializer)
        included_resources = copy.copy(included_resources)
        included_resources = [inflection.underscore(value) for value in included_resources]

        for field_name, field in six.iteritems(fields):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # Skip fields without relations or serialized data
            if not isinstance(
                    field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)
            ):
                continue

            try:
                included_resources.remove(field_name)
            except ValueError:
                # Skip fields not in requested included resources
                # If no child field, directly continue with the next field
                if field_name not in [node.split('.')[0] for node in included_resources]:
                    continue

            relation_instance = cls.extract_relation_instance(
                field_name, field, resource_instance, current_serializer
            )
            if isinstance(relation_instance, Manager):
                relation_instance = relation_instance.all()

            serializer_data = resource.get(field_name)

            if isinstance(field, relations.ManyRelatedField):
                serializer_class = included_serializers[field_name]
                field = serializer_class(relation_instance, many=True, context=context)
                serializer_data = field.data

            if isinstance(field, relations.RelatedField):
                if relation_instance is None:
                    continue

                many = field._kwargs.get('child_relation', None) is not None

                if isinstance(field, ResourceRelatedField) and not many:
                    already_included = serializer_data['type'] in included_cache and \
                        serializer_data['id'] in included_cache[serializer_data['type']]

                    if already_included:
                        continue

                serializer_class = included_serializers[field_name]
                field = serializer_class(relation_instance, many=many, context=context)
                serializer_data = field.data

            new_included_resources = [key.replace('%s.' % field_name, '', 1)
                                      for key in included_resources
                                      if field_name == key.split('.')[0]]

            if isinstance(field, ListSerializer):
                serializer = field.child
                relation_type = utils.get_resource_type_from_serializer(serializer)
                relation_queryset = list(relation_instance)

                if serializer_data:
                    for position in range(len(serializer_data)):
                        serializer_resource = serializer_data[position]
                        nested_resource_instance = relation_queryset[position]
                        resource_type = (
                            relation_type or
                            utils.get_resource_type_from_instance(nested_resource_instance)
                        )
                        serializer_fields = utils.get_serializer_fields(
                            serializer.__class__(
                                nested_resource_instance, context=serializer.context
                            )
                        )
                        new_item = cls.build_json_resource_obj(
                            serializer_fields,
                            serializer_resource,
                            nested_resource_instance,
                            resource_type,
                            getattr(serializer, '_poly_force_type_resolution', False)
                        )
                        included_cache[new_item['type']][new_item['id']] = \
                            utils._format_object(new_item)
                        cls.extract_included(
                            serializer_fields,
                            serializer_resource,
                            nested_resource_instance,
                            new_included_resources,
                            included_cache,
                        )

            if isinstance(field, Serializer):
                relation_type = utils.get_resource_type_from_serializer(field)

                # Get the serializer fields
                serializer_fields = utils.get_serializer_fields(field)
                if serializer_data:
                    new_item = cls.build_json_resource_obj(
                        serializer_fields,
                        serializer_data,
                        relation_instance,
                        relation_type,
                        getattr(field, '_poly_force_type_resolution', False)
                    )
                    included_cache[new_item['type']][new_item['id']] = utils._format_object(
                        new_item
                    )
                    cls.extract_included(
                        serializer_fields,
                        serializer_data,
                        relation_instance,
                        new_included_resources,
                        included_cache,
                    )

    @classmethod
    def extract_meta(cls, serializer, resource):
        """
        Gathers the data from serializer fields specified in meta_fields and adds it to
        the meta object.
        """
        if hasattr(serializer, 'child'):
            meta = getattr(serializer.child, 'Meta', None)
        else:
            meta = getattr(serializer, 'Meta', None)
        meta_fields = getattr(meta, 'meta_fields', [])
        data = OrderedDict()
        for field_name in meta_fields:
            data.update({
                field_name: resource.get(field_name)
            })
        return data

    @classmethod
    def extract_root_meta(cls, serializer, resource):
        """
        Calls a `get_root_meta` function on a serializer, if it exists.
        """
        many = False
        if hasattr(serializer, 'child'):
            many = True
            serializer = serializer.child

        data = {}
        if getattr(serializer, 'get_root_meta', None):
            json_api_meta = serializer.get_root_meta(resource, many)
            assert isinstance(json_api_meta, dict), 'get_root_meta must return a dict'
            data.update(json_api_meta)
        return data

    @classmethod
    def build_json_resource_obj(cls, fields, resource, resource_instance, resource_name,
                                force_type_resolution=False):
        """
        Builds the resource object (type, id, attributes) and extracts relationships.
        """
        # Determine type from the instance if the underlying model is polymorphic
        if force_type_resolution:
            resource_name = utils.get_resource_type_from_instance(resource_instance)
        resource_data = [
            ('type', resource_name),
            ('id', encoding.force_text(resource_instance.pk) if resource_instance else None),
            ('attributes', cls.extract_attributes(fields, resource)),
        ]
        relationships = cls.extract_relationships(fields, resource, resource_instance)
        if relationships:
            resource_data.append(('relationships', relationships))
        # Add 'self' link if field is present and valid
        if api_settings.URL_FIELD_NAME in resource and \
                isinstance(fields[api_settings.URL_FIELD_NAME], relations.RelatedField):
            resource_data.append(('links', {'self': resource[api_settings.URL_FIELD_NAME]}))
        return OrderedDict(resource_data)

    def render_relationship_view(self, data, accepted_media_type=None, renderer_context=None):
        # Special case for RelationshipView
        view = renderer_context.get("view", None)
        render_data = OrderedDict([
            ('data', data)
        ])
        links = view.get_links()
        if links:
            render_data.update({'links': links}),
        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )

    def render_errors(self, data, accepted_media_type=None, renderer_context=None):
        return super(JSONRenderer, self).render(
            utils.format_errors(data), accepted_media_type, renderer_context
        )

    def render(self, data, accepted_media_type=None, renderer_context=None):

        renderer_context = renderer_context or {}

        view = renderer_context.get("view", None)
        request = renderer_context.get("request", None)

        # Get the resource name.
        resource_name = utils.get_resource_name(renderer_context)

        # If this is an error response, skip the rest.
        if resource_name == 'errors':
            return self.render_errors(data, accepted_media_type, renderer_context)

        # if response.status_code is 204 then the data to be rendered must
        # be None
        response = renderer_context.get('response', None)
        if response is not None and response.status_code == 204:
            return super(JSONRenderer, self).render(
                None, accepted_media_type, renderer_context
            )

        from rest_framework_json_api.views import RelationshipView
        if isinstance(view, RelationshipView):
            return self.render_relationship_view(data, accepted_media_type, renderer_context)

        # If `resource_name` is set to None then render default as the dev
        # wants to build the output format manually.
        if resource_name is None or resource_name is False:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context
            )

        json_api_data = data
        # initialize json_api_meta with pagination meta or an empty dict
        json_api_meta = data.get('meta', {}) if isinstance(data, dict) else {}
        included_cache = defaultdict(dict)

        if data and 'results' in data:
            serializer_data = data["results"]
        else:
            serializer_data = data

        serializer = getattr(serializer_data, 'serializer', None)

        included_resources = utils.get_included_resources(request, serializer)

        if serializer is not None:

            # Extract root meta for any type of serializer
            json_api_meta.update(self.extract_root_meta(serializer, serializer_data))

            if getattr(serializer, 'many', False):
                json_api_data = list()

                for position in range(len(serializer_data)):
                    resource = serializer_data[position]  # Get current resource
                    resource_instance = serializer.instance[position]  # Get current instance

                    if isinstance(serializer.child, rest_framework_json_api.
                                  serializers.PolymorphicModelSerializer):
                        resource_serializer_class = serializer.child.\
                            get_polymorphic_serializer_for_instance(resource_instance)(
                                context=serializer.child.context
                            )
                    else:
                        resource_serializer_class = serializer.child

                    fields = utils.get_serializer_fields(resource_serializer_class)
                    force_type_resolution = getattr(
                        resource_serializer_class, '_poly_force_type_resolution', False)

                    json_resource_obj = self.build_json_resource_obj(
                        fields, resource, resource_instance, resource_name, force_type_resolution
                    )
                    meta = self.extract_meta(serializer, resource)
                    if meta:
                        json_resource_obj.update({'meta': utils._format_object(meta)})
                    json_api_data.append(json_resource_obj)

                    self.extract_included(
                        fields, resource, resource_instance, included_resources, included_cache
                    )
            else:
                fields = utils.get_serializer_fields(serializer)
                force_type_resolution = getattr(serializer, '_poly_force_type_resolution', False)

                resource_instance = serializer.instance
                json_api_data = self.build_json_resource_obj(
                    fields, serializer_data, resource_instance, resource_name, force_type_resolution
                )

                meta = self.extract_meta(serializer, serializer_data)
                if meta:
                    json_api_data.update({'meta': utils._format_object(meta)})

                self.extract_included(
                    fields, serializer_data, resource_instance, included_resources, included_cache
                )

        # Make sure we render data in a specific order
        render_data = OrderedDict()

        if isinstance(data, dict) and data.get('links'):
            render_data['links'] = data.get('links')

        # format the api root link list
        if view.__class__ and view.__class__.__name__ == 'APIRoot':
            render_data['data'] = None
            render_data['links'] = json_api_data
        else:
            render_data['data'] = json_api_data

        if included_cache:
            if isinstance(json_api_data, list):
                objects = json_api_data
            else:
                objects = [json_api_data]

            for object in objects:
                obj_type = object.get('type')
                obj_id = object.get('id')
                if obj_type in included_cache and \
                   obj_id in included_cache[obj_type]:
                    del included_cache[obj_type][obj_id]
                if not included_cache[obj_type]:
                    del included_cache[obj_type]

        if included_cache:
            render_data['included'] = list()
            for included_type in sorted(included_cache.keys()):
                for included_id in sorted(included_cache[included_type].keys()):
                    render_data['included'].append(included_cache[included_type][included_id])

        if json_api_meta:
            render_data['meta'] = utils._format_object(json_api_meta)

        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )
