# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from django_fixtureboy import Contract, FactoryEmitter
        # todo: add hook via settings.
        Contract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_subfactory_hook")
        Contract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_modelutils_choices_hook")
        Contract.finish.add_hook("django_fixtureboy.hooks:finish_add_autopep8_hook")
        from django.apps import apps
        emitter = FactoryEmitter(apps.get_models(), Contract)
        result = emitter.emit()
        print(result)
