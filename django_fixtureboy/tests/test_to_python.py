# -*- coding:utf-8 -*-
from evilunit import test_target
from django_fixtureboy.testing import CleanHookTestCase


@test_target("django_fixtureboy.codegen:ValueDeserializerEmitter")
class Tests(CleanHookTestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models
        from jsonfield import JSONField

        class Item(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            price = models.IntegerField()
            pull_date = models.DateTimeField(auto_now_add=True)
            memo = JSONField()

            class Meta:
                app_label = __name__

        cls.Item = Item

    def _makeOne(self, models):
        from django_fixtureboy import Contract
        contract = Contract(models)
        return self._getTarget()(contract)

    def test_it_class_definition(self):
        import datetime
        models = [self.Item]
        emitter = self._makeOne(models)

        code = emitter.emit_class()

        env = {}
        exec(str(code), env)
        Deserializer = env[emitter.classname()]

        result = Deserializer.datetime("2014-10-30T14:49:57.460464")
        self.assertIsInstance(result, datetime.datetime)

    def test_it_use_method__datetime(self):
        models = [self.Item]
        emitter = self._makeOne(models)

        code = str(emitter.convert_value(self.Item, "pull_date", "2014-10-30T14:49:57.460464"))
        self.assertRegex(code, "{}.datetime\('2014-.+64'\)".format(emitter.classname()))

    def test_it_use_method__integer(self):
        models = [self.Item]
        emitter = self._makeOne(models)

        code = emitter.convert_value(self.Item, "price", "200")
        self.assertEqual(code, 200)

    def test_it_use_method__json(self):
        models = [self.Item]
        emitter = self._makeOne(models)

        code = str(emitter.convert_value(self.Item, "memo", '{"description": "healing?"}'))
        self.assertRegex(code, "{}.json(.+)".format(emitter.classname()))

    def test_it_use_method__json__with_hook(self):
        from django_fixtureboy import Contract
        Contract.on_setup.add_hook("django_fixtureboy.hooks:setup_add_jsonfield_hook")
        models = [self.Item]
        emitter = self._makeOne(models)

        code = emitter.convert_value(self.Item, "memo", '{"description": "healing?"}')
        self.assertEqual(code, '{"description": "healing?"}')
