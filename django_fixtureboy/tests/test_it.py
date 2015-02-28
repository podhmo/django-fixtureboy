# -*- coding:utf-8 -*-
from evilunit import test_target
from django_fixtureboy.testing import CleanHookTestCase


@test_target("django_fixtureboy:FactoryEmitter")
class Tests(CleanHookTestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models

        class Group(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

        class Member(models.Model):
            group = models.ForeignKey(Group)
            name = models.CharField(max_length=255, null=False, default="")

        cls.Group = Group
        cls.Member = Member

    def _get_models(self):
        return [self.Member, self.Group]

    def test_it(self):
        from django_fixtureboy import DefaultContract
        from django_fixtureboy.hooks import attrs_add_subfactory_hook
        DefaultContract.attrs.add_hook(attrs_add_subfactory_hook)

        emitter = self._makeOne(self._get_models(), DefaultContract)
        result = emitter.emit()
        print(result)
