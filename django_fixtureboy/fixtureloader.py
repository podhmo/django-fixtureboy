# -*- coding:utf-8 -*-
from io import StringIO
from xml.dom import pulldom
from django.core.serializers.xml_serializer import (
    DefusedExpatParser,
    getInnerText
)


class ObjectSerializer(object):
    def serialize(self, obj):
        model = obj._meta.concrete_model
        D = {}
        for field in model._meta.local_fields:
            if field.serialize:
                if field.rel is None:
                    D[field.name] = field.value_to_string(obj)
                else:
                    D[field.name] = field.value_to_string(obj)  # xxx
        return D


class ObjectListToDictHandler(object):
    def __init__(self, objlist, contract):
        self.objlist = objlist
        self.contract = contract
        self.current_model = None  # hmm
        self.serializer = ObjectSerializer()

    def __iter__(self):
        for obj in self.objlist:
            Model = self.current_model = obj.__class__
            self.contract.on_model_detected(Model)
            yield self.serializer.serialize(obj)


class XMLToDictHandler(object):
    def __init__(self, stream, contract):
        self.stream = stream
        self.contract = contract
        self.event_stream = pulldom.parse(stream, DefusedExpatParser())
        self.current_model = None  # hmm

    def __iter__(self):
        return self

    def __next__(self):
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "object":
                self.event_stream.expandNode(node)
                return self.handle_object(node)
        raise StopIteration

    def handle_object(self, node):
        self.current_model = Model = self._get_model_from_node(node, "model")
        self.contract.on_model_detected(Model)
        data = {}
        if node.hasAttribute('pk'):
            data[Model._meta.pk.attname] = node.getAttribute('pk')

        model_fields = Model._meta.get_all_field_names()
        for field_node in node.getElementsByTagName("field"):
            field_name = field_node.getAttribute("name")
            if field_name not in model_fields:
                continue
            if field_node.getElementsByTagName('None'):
                value = None
            else:
                value = getInnerText(field_node).strip()
            data[field_name] = value
        return data

    def _get_model_from_node(self, node, attr):
        model_identifier = node.getAttribute(attr)
        return self.contract.get_model(model_identifier)


class FixtureDataIterator(object):
    # todo: supprot zip .etc
    def __init__(self, stream_or_string, contract, handler_factory=XMLToDictHandler):
        if not hasattr(stream_or_string, "read"):
            stream_or_string = StringIO(stream_or_string)
        self.contract = contract
        self.handler = handler_factory(stream_or_string, contract)

    def __iter__(self):
        for datum in self.handler:
            yield (self.handler.current_model, datum)
