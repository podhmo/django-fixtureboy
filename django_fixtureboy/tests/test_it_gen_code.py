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
        import django
        django.setup()
        g = self.Group(id=1, name="G", color=self.Group.COLOR_LIST.r)
        g.save()
        m0 = self.Member(name="HP", group=g)
        m0.save()
        m1 = self.Member(name="RW", group=g)
        m1.save()

        from django_fixtureboy import Contract
        from django_fixtureboy.fixtureloader import ObjectListToDictIterator
        iterator = ObjectListToDictIterator([m0, m1, g], Contract())

        # todo: 必要な要素だけ集める
        # from django_mindscape import Walker, ModelMapProvider
        # provider = ModelMapProvider(Walker([self.Member]))

