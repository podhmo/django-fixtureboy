# -*- coding:utf-8 -*-
import unittest


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models
        from model_utils import Choices

        class Group(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            COLOR_LIST = Choices((0, "r", "red"), (2, "g", "green"), (3, "b", "blue"))
            color = models.IntegerField(choices=COLOR_LIST)

            class Meta:
                app_label = __name__

        class Permission(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

            class Meta:
                app_label = __name__

        class Member(models.Model):
            group = models.ForeignKey(Group)
            permission_set = models.ManyToManyField(Permission)
            name = models.CharField(max_length=255, null=False, default="")

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
        g = self.Group(id=1, name="G", color=self.Group.COLOR_LIST.r)
        g.save()
        m0 = self.Member(name="HP", group=g)
        m0.save()
        m1 = self.Member(name="RW", group=g)
        m1.save()

        from django_fixtureboy import Contract
        from django_fixtureboy.fixtureloader import ObjectListToDictIterator
        from django_fixtureboy.codegen import CodeGenerator, OrderedIterator
        from django_mindscape import Walker, ModelMapProvider
        provider = ModelMapProvider(Walker([self.Member]))
        contract = Contract(provider.ordered_models)
        iterator = ObjectListToDictIterator([m0, m1, g], contract)
        codegen = CodeGenerator(OrderedIterator(iterator, provider), contract)
        result = (str(codegen.generate()))
        # TODO: tidy test
        expected = """
group0 = GroupFactory(id='1', name='G', color='0')
member0 = MemberFactory(id='1', group=group0, name='HP')
member1 = MemberFactory(id='2', group=group0, name='RW')
"""
        self.assertEqual(expected.strip(), result.strip())
