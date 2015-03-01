# -*- coding:utf-8 -*-
import unittest


class Tests(unittest.TestCase):
    def _getTarget(self):
        from django_fixtureboy.hooks import args_add_modelutils_choices_hook
        return args_add_modelutils_choices_hook

    def _callFUT(self, *args, **kwargs):
        return self._getTarget()(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        from django.db import models
        from model_utils import Choices

        class model(models.Model):
            JA_LIST = Choices(("0", "hai", u"はい"), ("1", "oo", u"おお"))
            EN_LIST = Choices(("0", "yes", u"yes"), ("1", "hmm", u"hmm"))
            FLAG = Choices((0, "off"), (1, "on"))
            ja = models.CharField(choices=JA_LIST)
            en = models.CharField(choices=EN_LIST)
            flag = models.SmallIntegerField(choices=FLAG)
            flag2 = models.SmallIntegerField(choices=Choices((0, "off"), (1, "on")))
            flag3 = models.SmallIntegerField(choices=((0, "off"), (1, "on")))

        cls.model = model

    def test_ja(self):
        contract = None
        gen = lambda: "0"
        field = [f for f in self.model._meta.fields if f.name == "ja"][0]
        result = self._callFUT(contract, gen, self.model, field, "0")
        self.assertEqual(str(result), "model.JA_LIST.hai")

    def test_en(self):
        contract = None
        gen = lambda: "0"
        field = [f for f in self.model._meta.fields if f.name == "en"][0]
        result = self._callFUT(contract, gen, self.model, field, "0")
        self.assertEqual(str(result), "model.EN_LIST.yes")

    def test_en__missing_value(self):
        contract = None
        gen = lambda: ""
        field = [f for f in self.model._meta.fields if f.name == "en"][0]
        result = self._callFUT(contract, gen, self.model, field, "")
        self.assertEqual(str(result), "model.EN_LIST.yes")

    def test_flag(self):
        contract = None
        gen = lambda: 0
        field = [f for f in self.model._meta.fields if f.name == "flag"][0]
        result = self._callFUT(contract, gen, self.model, field, 0)
        self.assertEqual(result, 0)

    def test_flag2(self):
        contract = None
        gen = lambda: 0
        field = [f for f in self.model._meta.fields if f.name == "flag2"][0]
        result = self._callFUT(contract, gen, self.model, field, 0)
        self.assertEqual(result, 0)

    def test_flag3(self):
        contract = None
        gen = lambda: 0
        field = [f for f in self.model._meta.fields if f.name == "flag3"][0]
        result = self._callFUT(contract, gen, self.model, field, 0)
        self.assertEqual(result, 0)
