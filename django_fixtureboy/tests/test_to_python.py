# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target


@test_target("django_fixtureboy.codegen:ValueDeserializerEmitter")
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models

        class Item(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            price = models.IntegerField()
            pull_date = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = __name__

        cls.Item = Item

    def _makeOne(self, models):
        from django_fixtureboy import DefaultContract
        contract = DefaultContract()
        return self._getTarget()(models, contract)

    def test_it_class_definition(self):
        import datetime
        models = [self.Item]
        emitter = self._makeOne(models)

        code = emitter.emit_class_definition()

        env = {}
        exec(code, env)
        Deserializer = env[emitter.classname()]

        result = Deserializer.datetime("2014-10-30T14:49:57.460464")
        self.assertIsInstance(result, datetime.datetime)

    def test_it_use_method(self):
        models = [self.Item]
        emitter = self._makeOne(models)

        code = emitter.emit_method_call(self.Item, "pull_date", "2014-10-30T14:49:57.460464")
        self.assertRegex(code, "{}.datetime\('2014-.+64'\)".format(emitter.classname()))
