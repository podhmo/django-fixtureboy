# -*- coding:utf-8 -*-
import unittest
from django_fixtureboy.testing import CleanHookTestCase


class Tests(CleanHookTestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models
        from model_utils import Choices

        class Group(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            COLOR_LIST = Choices((0, "r", "red"), (2, "g", "green"), (3, "b", "blue"))
            color = models.IntegerField(choices=COLOR_LIST)
            ctime = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = __name__

        class Permission(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            ctime = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = __name__

        class Member(models.Model):
            group = models.ForeignKey(Group)
            permission_set = models.ManyToManyField(Permission)
            name = models.CharField(max_length=255, null=False, default="")
            ctime = models.DateTimeField(auto_now_add=True)
            birth = models.DateField()

            class Meta:
                app_label = __name__

        cls.Member = Member
        cls.Group = Group

        # create table
        from django_fixtureboy.testing import create_table
        create_table(Member)
        create_table(Group)
        create_table(Permission)

    def test_it(self):
        from datetime import date
        g = self.Group(id=1, name="G", color=self.Group.COLOR_LIST.r)
        g.save()
        m0 = self.Member(name="HP", group=g, birth=date(1990, 1, 1))
        m0.save()
        m1 = self.Member(name="RW", group=g, birth=date(1990, 1, 1))
        m1.save()

        from django_fixtureboy import Contract
        from django_fixtureboy.fixtureloader import ObjectListToDictIterator
        from django_fixtureboy.codegen import CodeGenerator, OrderedIterator
        from django_mindscape import Walker, ModelMapProvider
        Contract.args.add_hook("django_fixtureboy.hooks:args_add_modelutils_choices_hook")
        Contract.finish.add_hook("django_fixtureboy.hooks:finish_add_autopep8_hook")
        from django_fixtureboy.hooks import BuildDataOmmitingHook
        Contract.on_build_data.add_hook(BuildDataOmmitingHook("ctime"))

        provider = ModelMapProvider(Walker([self.Member]))
        contract = Contract(provider.ordered_models)
        iterator = ObjectListToDictIterator([m0, m1, g], contract)
        codegen = CodeGenerator(OrderedIterator(iterator, provider), contract)
        result = str(codegen.generate())
        # TODO: tidy test
        print(result)
        expected = """
from factory.django import DjangoModelFactory
from django.db.models.fields import DateField
from django.db.models.fields import DateTimeField


class DD(object):
    date = staticmethod(DateField().to_python)
    datetime = staticmethod(DateTimeField().to_python)

group0 = GroupFactory(id=1, name='G', color=Group.COLOR_LIST.r)
member0 = MemberFactory(
    id=1, group=group0, name='HP', birth=DD.date('1990-01-01'))
member1 = MemberFactory(
    id=2, group=group0, name='RW', birth=DD.date('1990-01-01'))
"""
        self.assertEqual(expected.strip(), result.strip())
