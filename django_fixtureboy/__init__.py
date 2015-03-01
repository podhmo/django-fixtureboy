# -*- coding:utf-8 -*-
from factory.django import DjangoModelFactory
from .langhelpers import PythonModule
from django.apps import apps
from collections import namedtuple
from functools import partial
from .hookpoint import withhook, HasHookPointMeta
from .hookpoint import clearall_hooks
from .codegen import eager
from .structure import OrderedSet


class Contract(HasHookPointMeta("_BaseHookPoint", (), {})):
    def __init__(self, models, base_factory=DjangoModelFactory):
        self.models = models
        self.base_factory = base_factory
        self.initial_parts = CodeParts(
            lib=OrderedSet([self.build_import_sentence(base_factory)]),
            name=None,
            model=None,
            bases=None,
            attrs=[]
        )

    def build_import_sentence(self, x):
        return "from {} import {}".format(x.__module__, x.__name__)

    @withhook
    def name(self, model):
        return "{}Factory".format(model.__name__)

    @withhook
    def bases(self, model):
        return self.base_factory.__name__

    @withhook
    def attrs(self, model):
        return []

    @withhook
    def lib(self, model):
        return [self.build_import_sentence(model)]

    @withhook
    def parts(self, model):
        return CodeParts(
            lib=self.lib(model),
            name=self.name(model),
            model=model.__name__,
            bases=self.bases(model),
            attrs=self.attrs(model)
        )

    @withhook
    def gen_meta(self, m, parts):
        with m.class_("Meta"):
            m.stmt("model = {}".format(parts.model))

    @withhook
    def finish(self, m):
        return str(m)

    # for fixture loader
    @withhook
    def on_model_detected(self, model):
        self.initial_parts.lib.add(self.build_import_sentence(model))

    @withhook
    def on_build_data(self, model, data):
        return data

    def get_model(self, model_identifier):
        from django.apps import apps
        return apps.get_model(model_identifier)

    # for ValueDeserializer
    @withhook
    def on_setup(self, emitter):
        from django.db.models.fields import (
            AutoField,
            IntegerField,
            CharField,
            BooleanField
        )
        emitter.alias_map[AutoField.__name__] = eager(partial(AutoField.to_python, None))
        emitter.alias_map[IntegerField.__name__] = eager(partial(IntegerField.to_python, None))
        emitter.alias_map[CharField.__name__] = eager(partial(CharField.to_python, None))
        emitter.alias_map[BooleanField.__name__] = eager(partial(BooleanField.to_python, None))

    def alias_from_field(self, f):
        return f.__class__.__name__.replace("Field", "").lower()

    def keyname_from_field(self, f):
        return f.__class__.__name__

    def deserializer_name(self):
        return "DD"

    # variable manager
    def varname(self, model, i):
        return "{}{}".format(model.__name__.lower(), i)

    @withhook
    def args(self, model, field, value):
        return value

    def create_model(self, m, model, varname, args):
        # TODO: add import sentence
        factory_name = self.name(model)
        with m.call("{} = {}".format(varname, factory_name)) as r:
            for arg in args:
                r.append(arg)
        return m

CodeParts = namedtuple("CodeParts", "lib name model bases attrs")  # xxx


class FactoryEmitter(object):
    def __init__(self, models=None, contract_factory=None, base_factory=DjangoModelFactory):
        self.models = models or apps.get_models()
        self.contract_factory = contract_factory or Contract
        self.base_factory = base_factory
        self.contract = self.contract_factory(self.models, self.base_factory)
        self.parts = [self.contract.initial_parts]

    def collect_parts(self):
        for m in self.models:
            self.parts.append(self.contract.parts(m))

    def emit(self):
        self.collect_parts()
        m = PythonModule()

        for parts in self.parts:
            for import_sentence in parts.lib:
                m.stmt(import_sentence)
        m.sep()

        for parts in self.parts:
            if parts.name is None:
                continue
            with m.class_(parts.name, bases=parts.bases):
                for attr in parts.attrs:
                    if callable(attr):
                        attr(m)
                    else:
                        m.stmt(attr)

                m.sep()

                self.contract.gen_meta(m, parts)
                m.sep()
        return self.contract.finish(m)
