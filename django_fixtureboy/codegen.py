# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from collections import defaultdict, namedtuple, Counter
from srcgen.python import PythonModule

eager = namedtuple("eager", "fn")


class ReprWrapper(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)


class VariableManager(object):
    def __init__(self, contract):
        self.contract = contract
        self.counters = Counter()  # model -> int
        self.variables = defaultdict(dict)  # model -> primary key -> varname

    def generate_variable(self, model, pk):
        i = self.counters[model]
        self.counters[model] += 1
        varname = self.contract.varname(model, i)
        self.variables[model][pk] = varname
        return varname

    def get_variable(self, model, pk):
        return self.variables[model].get(pk)


class CodeGenerator(object):
    """温かみのある手書きのコード"""
    def __init__(self, iterator, contract):
        self.iterator = iterator
        self.contract = contract
        self.value_emitter = ValueDeserializerEmitter(contract)
        self.variable_manager = VariableManager(contract)

    def _get_primary_key(self, model, data):
        """hmm"""
        return data[model._meta.pk.name]  # hmm

    def _get_creation_args(self, model, data):
        args = []
        for name, value in data.items():
            f = self.value_emitter.get_field(model, name)
            if f.rel is None:
                args.append("{}={!r}".format(name, self.value_emitter.convert_value(model, name, value)))
            else:
                args.append("{}={}".format(name, self.variable_manager.get_variable(f.rel.to, value)))
        return args

    def generate(self, m=None):
        m = m or PythonModule()
        for import_sentence in self.contract.initial_parts.lib:
            m.stmt(import_sentence)

        self.value_emitter.emit_class(m)

        m.sep()

        for model, data in self.iterator:
            pk = self._get_primary_key(model, data)
            varname = self.variable_manager.generate_variable(model, pk)
            args = self._get_creation_args(model, data)
            self.contract.create_model(m, model, varname, args)
        return self.contract.finish(m)


class OrderedIterator(object):
    def __init__(self, iterator, model_map_provider):
        self.objects = defaultdict(list)
        self.iterator = iterator
        self.model_map_provider = model_map_provider

    def __iter__(self):
        for model, data in self.iterator:
            self.objects[model].append(data)
        for model in self.model_map_provider.ordered_models:
            for data in self.objects[model]:
                yield model, data


class ValueDeserializerEmitter(object):
    def __init__(self, contract):
        self.contract = contract
        self.models = contract.models
        self.model_fields_map = defaultdict(dict)  # model -> dict(fieldname -> field)
        self.alias_map = {}  # field-class-name -> methodname or eager(fn)
        self.fields = {}     # field-class-name -> field
        self.setup()

    def get_field(self, model, fieldname):  # xxx:
        return self.model_fields_map[model][fieldname]

    def setup(self):
        alias_from_field = self.contract.alias_from_field
        keyname_from_field = self.contract.keyname_from_field

        for model in self.models:
            field_map = self.model_fields_map[model]
            for f in model._meta.local_fields:
                field_map[f.name] = f
                if f.rel is None:
                    name = keyname_from_field(f)
                    self.alias_map[name] = alias_from_field(f)
                    self.fields[name] = f.__class__
            for f in model._meta.local_many_to_many:
                field_map[f.name] = f
        self.contract.on_setup(self)

    def classname(self):
        return self.contract.deserializer_name()

    def emit_class(self, m=None):
        m = m or PythonModule()
        # import
        for name, fieldclass in self.fields.items():
            alias = self.alias_map[name]
            if not isinstance(alias, eager):
                m.stmt(self.contract.build_import_sentence(fieldclass))

        m.sep()

        with m.class_(self.classname()):
            has_attribute = False
            for name in self.fields.keys():
                alias = self.alias_map[name]
                if not isinstance(alias, eager):
                    has_attribute = True
                    m.stmt("{alias} = staticmethod({clsname}().to_python)".format(alias=alias, clsname=name))
            if not has_attribute:
                m.stmt("pass")
        return m

    def convert_value(self, model, fieldname, value):
        contract = self.contract
        field = self.model_fields_map[model][fieldname]
        keyname = contract.keyname_from_field(field)
        alias = self.alias_map[keyname]
        if isinstance(alias, eager):
            return self.contract.args(model, field, alias.fn(value))
        else:
            return ReprWrapper("{}.{}({!r})".format(self.classname(), alias, value))
