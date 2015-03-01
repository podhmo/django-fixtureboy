# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from factory.django import DjangoModelFactory
from collections import namedtuple
import contextlib
from functools import partial
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured
from .hookpoint import withhook, HasHookPointMeta, clearall_hooks
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


def get_provider(models=None, brain=None):
    from django_mindscape import ModelMapProvider, Walker, Brain
    from django.apps import apps
    models = models or apps.get_models()
    return ModelMapProvider(Walker(models, brain=brain or Brain()))


class Application(object):
    def __init__(self, provider, settings, key="FIXTUREBOY_CONTRACT_SETTINGS"):
        self.provider = provider  # provider is django_mindscape.ModelMapProvider
        self.settings = settings
        self.key = key

    @cached_property
    def contract(self):
        try:
            options = getattr(self.settings, self.key)
            return self.construct_contract_from_options(options)
        except AttributeError:
            raise ImproperlyConfigured("please adding settings.{}".format(self.key))

    def construct_contract_from_options(self, options):
        class _Contract(Contract):
            pass
        for name, hooks in options.items():
            if not hasattr(_Contract, name):
                logger.info("Contract.%s is not found. ignored.", name)
                continue
            for hook in hooks:
                getattr(_Contract, name).add_hook(hook)
        return _Contract(self.provider.ordered_models)

    @contextlib.contextmanager
    def factory_generator(self):
        from .factorygen import FactoryGenerator
        yield FactoryGenerator(self.contract)

    @contextlib.contextmanager
    def xml_code_generator(self, xml):
        from .fixtureloader import XMLToDictIterator
        from .codegen import OrderedIterator, CodeGenerator
        with open(xml) as rf:
            iterator = OrderedIterator(XMLToDictIterator(rf, self.contract), self.provider)
            yield CodeGenerator(iterator, self.contract)

    @contextlib.contextmanager
    def object_code_generator(self, objlist):
        from .fixtureloader import ObjectListToDictIterator
        from .codegen import OrderedIterator, CodeGenerator
        iterator = OrderedIterator(ObjectListToDictIterator(objlist, self.contract), self.provider)
        yield CodeGenerator(iterator, self.contract)


__all__ = [
    "clearall_hooks",
    "withhook",
    "Contract"
]
