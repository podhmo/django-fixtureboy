# -*- coding:utf-8 -*-
from evilunit import test_target
from django_fixtureboy.testing import CleanHookTestCase


@test_target("django_fixtureboy:FactoryEmitter")
class Tests(CleanHookTestCase):
    @classmethod
    def setUpClass(cls):
        from django.db import models
        from model_utils import Choices

        class Group(models.Model):
            name = models.CharField(max_length=255, null=False, default="")
            COLOR_LIST = Choices((0, "r", "red"), (2, "g", "green"), (3, "b", "blue"))
            color = models.IntegerField(choices=COLOR_LIST)
            ONOFF = Choices((True, "on"), (False, "off"))
            active = models.BooleanField(choices=ONOFF)
            gender = models.CharField(max_length=1, choices=["f", "m"])

        class Permission(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

        class Skill(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

        class Member(models.Model):
            group = models.ForeignKey(Group)
            permission_set = models.ManyToManyField(Permission)
            skill_set = models.ManyToManyField(Skill, through="MemberToSkill")
            name = models.CharField(max_length=255, null=False, default="")

        class MemberToSkill(models.Model):
            member = models.ForeignKey(Member)
            skill = models.ForeignKey(Skill)

        cls.Group = Group
        cls.Member = Member

    def _get_models(self):
        return [self.Member, self.Group]

    def test_it(self):
        from django_fixtureboy import Contract
        Contract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_subfactory_hook")
        Contract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_modelutils_choices_hook")
        Contract.attrs.add_hook("django_fixtureboy.hooks:attrs_add_many_to_many_post_generation_hook")
        Contract.finish.add_hook("django_fixtureboy.hooks:finish_add_autopep8_hook")
        emitter = self._makeOne(self._get_models(), Contract)
        result = emitter.emit()
        print(result)
