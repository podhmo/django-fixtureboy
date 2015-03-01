# -*- coding:utf-8 -*-
from factory.django import DjangoModelFactory
from srcgen.python import PythonModule
from django.apps import apps
from collections import namedtuple
from functools import partial
from .hookpoint import withhook, HasHookPointMeta
from .hookpoint import clearall_hooks
from .codegen import eager

class DefaultContract(HasHookPointMeta("_BaseHookPoint", (), {})):
    def __init__(self, base_factory=DjangoModelFactory):
        self.base_factory = base_factory
        self.initial_parts = CodeParts(
            lib=set([self.build_import_sentence(base_factory)]),
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

    # for ValueDeserializer
    @withhook
    def setup(self, emitter):
        from django.db.models.fields import (
            AutoField,
            IntegerField,
            CharField
        )
        emitter.alias_map[AutoField.__name__] = eager(partial(AutoField.to_python, None))
        emitter.alias_map[IntegerField.__name__] = eager(partial(IntegerField.to_python, None))
        emitter.alias_map[CharField.__name__] = eager(partial(CharField.to_python, None))

    def alias_from_field(self, f):
        return f.__class__.__name__.replace("Field", "").lower()

    def keyname_from_field(self, f):
        return f.__class__.__name__

    def deserializer_name(self):
        return "DD"

CodeParts = namedtuple("CodeParts", "lib name model bases attrs")  # xxx


class FactoryEmitter(object):
    def __init__(self, models=None, contract_factory=None, base_factory=DjangoModelFactory):
        self.models = models or apps.get_models()
        self.contract_factory = contract_factory or DefaultContract
        self.base_factory = base_factory
        self.contract = self.contract_factory(self.base_factory)
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
