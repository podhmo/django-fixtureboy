# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from collections import defaultdict, namedtuple
from srcgen.python import PythonModule

eager = namedtuple("eager", "fn")


class CodeGenerator(object):
    """温かみのある手書きのコード"""
    def __init__(self, iterator, contract):
        self.iterator = iterator
        self.contract = contract
        self.value_emitter = ValueDeserializerEmitter(contract)

    def __iter__(self):
        pass


class ValueDeserializerEmitter(object):
    def __init__(self, contract):
        self.contract = contract
        self.models = contract.models
        self.model_fields_map = defaultdict(dict)  # model -> dict(fieldname -> field)
        self.alias_map = {}  # field-class-name -> methodname or eager(fn)
        self.fields = {}     # field-class-name -> field
        self.setup()

    def setup(self):
        alias_from_field = self.contract.alias_from_field
        keyname_from_field = self.contract.keyname_from_field

        for model in self.models:
            field_map = self.model_fields_map[model]
            for f in model._meta.local_fields:
                if f.rel is None:
                    name = keyname_from_field(f)
                    self.alias_map[name] = alias_from_field(f)
                    self.fields[name] = f.__class__
                    field_map[f.name] = f
        self.contract.on_setup(self)

    def classname(self):
        return self.contract.deserializer_name()

    def emit_class(self):
        m = PythonModule()
        # import
        for name, fieldclass in self.fields.items():
            alias = self.alias_map[name]
            if not isinstance(alias, eager):
                m.stmt(self.contract.build_import_sentence(fieldclass))

        m.sep()

        with m.class_(self.classname()):
            for name in self.fields.keys():
                alias = self.alias_map[name]
                if not isinstance(alias, eager):
                    m.stmt("{alias} = staticmethod({clsname}().to_python)".format(alias=alias, clsname=name))
        return str(m)

    def emit_value(self, model, fieldname, value):
        contract = self.contract
        field = self.model_fields_map[model][fieldname]
        keyname = contract.keyname_from_field(field)
        alias = self.alias_map[keyname]
        if isinstance(alias, eager):
            return "{}".format(alias.fn(value))
        else:
            return "{}.{}({!r})".format(self.classname(), alias, value)
