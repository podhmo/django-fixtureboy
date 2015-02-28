# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from django_fixtureboy import DefaultContract, FactoryEmitter
        # todo: add hook via settings.
        DefaultContract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_subfactory_hook")
        DefaultContract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_modelutils_choices_hook")
        DefaultContract.finish.add_hook("django_fixtureboy.hooks:finish_add_autopep8_hook")
        from django.apps import apps
        emitter = FactoryEmitter(apps.get_models(), DefaultContract)
        result = emitter.emit()
        print(result)
