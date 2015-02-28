# -*- coding:utf-8 -*-
from factory.django import DjangoModelFactory
from srcgen.python import PythonModule
from django.apps import apps
from django.utils.functional import cached_property
from django_mindscape import ModelMapProvider, Walker, Brain
from collections import namedtuple
from .hookpoint import withhook, HasHookPointMeta
from .hookpoint import clearall_hooks


class DefaultContract(HasHookPointMeta("_BaseHookPoint", (), {})):
    def __init__(self, model_map_provider, base_factory=DjangoModelFactory):
        self.provider = model_map_provider
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

    @property
    def brain(self):
        return self.provider.brain

    @property
    def models(self):
        return self.provider.ordered_models

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


CodeParts = namedtuple("CodeParts", "lib name model bases attrs")  # xxx


class FactoryEmitter(object):
    @cached_property
    def model_map_provider(self):
        return ModelMapProvider(Walker(self.models, Brain()))

    def __init__(self, models=None, contract_factory=None, base_factory=DjangoModelFactory):
        self.models = models or apps.get_models()
        self.contract_factory = contract_factory or DefaultContract
        self.base_factory = base_factory
        self.contract = self.contract_factory(self.model_map_provider, self.base_factory)
        self.parts = [self.contract.initial_parts]

    def collect_parts(self):
        for m in self.contract.models:
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
                    m.stmt(attr)

                self.contract.gen_meta(m, parts)
        return str(m)
