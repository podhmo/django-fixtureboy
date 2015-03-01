# -*- coding:utf-8 -*-
from evilunit import test_target
from django_fixtureboy.testing import CleanHookTestCase


@test_target("django_fixtureboy:Application")
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

            class Meta:
                app_label = __name__

        class Permission(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

            class Meta:
                app_label = __name__

        class Skill(models.Model):
            name = models.CharField(max_length=255, null=False, default="")

            class Meta:
                app_label = __name__

        class Member(models.Model):
            group = models.ForeignKey(Group)
            permission_set = models.ManyToManyField(Permission)
            skill_set = models.ManyToManyField(Skill, through="MemberToSkill")
            name = models.CharField(max_length=255, null=False, default="")

            class Meta:
                app_label = __name__

        class MemberToSkill(models.Model):
            member = models.ForeignKey(Member)
            skill = models.ForeignKey(Skill)

            class Meta:
                app_label = __name__

        cls.Group = Group
        cls.Member = Member

    def _get_models(self):
        return [self.Member, self.Group]

    def test_it(self):
        from django_fixtureboy import get_provider
        provider = get_provider(self._get_models())

        class settings:
            FIXTUREBOY_CONTRACT_SETTINGS = {
                "attrs": [
                    "django_fixtureboy.hooks:attrs_add_subfactory_hook",
                    "django_fixtureboy.hooks:attrs_add_modelutils_choices_hook",
                    "django_fixtureboy.hooks:attrs_add_many_to_many_post_generation_hook",
                ],
                "finish": [
                    "django_fixtureboy.hooks:finish_add_autopep8_hook"
                ]
            }
        app = self._makeOne(provider, settings)
        with app.factory_generator() as gen:
            result = gen.generate()
        # TODO: tidy test
        expected = """
from factory.django import DjangoModelFactory
from factory.declarations import SubFactory
from factory.helpers import post_generation
from django_fixtureboy.tests.test_it_gen_factory import Group
from django_fixtureboy.tests.test_it_gen_factory import Permission
from django_fixtureboy.tests.test_it_gen_factory import Member_permission_set
from django_fixtureboy.tests.test_it_gen_factory import Skill
from django_fixtureboy.tests.test_it_gen_factory import MemberToSkill
from django_fixtureboy.tests.test_it_gen_factory import Member


class GroupFactory(DjangoModelFactory):
    color = Group.COLOR_LIST.r  # red
    active = True  # on
    gender = 'f'

    class Meta(object):
        model = Group


class PermissionFactory(DjangoModelFactory):

    class Meta(object):
        model = Permission


class Member_permission_setFactory(DjangoModelFactory):
    member = SubFactory(Member)
    permission = SubFactory(Permission)

    class Meta(object):
        model = Member_permission_set


class SkillFactory(DjangoModelFactory):

    class Meta(object):
        model = Skill


class MemberToSkillFactory(DjangoModelFactory):
    member = SubFactory(Member)
    skill = SubFactory(Skill)

    class Meta(object):
        model = MemberToSkill


class MemberFactory(DjangoModelFactory):
    group = SubFactory(Group)

    @post_generation
    def permission_set(create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for x in extracted:
                self.permission_set.add(x)

    @post_generation
    def skill_set(create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for x in extracted:
                self.skill_set.add(x)

    class Meta(object):
        model = Member
"""
        self.assertEqual(result.strip(), expected.strip())
