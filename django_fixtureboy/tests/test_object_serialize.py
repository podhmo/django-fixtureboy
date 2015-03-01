# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target


@test_target("django_fixtureboy.codegen:ObjectSerializer")
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models

        class Category(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

            class Meta:
                app_label = __name__

        class Item(models.Model):
            category = models.ForeignKey(Category)
            name = models.CharField(max_length=255, null=False, default="")
            price = models.IntegerField()
            pull_date = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = __name__

        cls.Item = Item

    def test_it(self):
        from datetime import datetime
        item = self.Item(category_id=1, name="portion", price=200, pull_date=datetime(2000, 1, 1))
        target = self._makeOne()
        result = target.emit(item)
        expected = {'category': '1', 'price': '200', 'name': 'portion', 'pull_date': '2000-01-01T00:00:00'}
        self.assertEqual(result, expected)
