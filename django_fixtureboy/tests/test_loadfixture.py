# -*- coding:utf-8 -*-
from evilunit import test_target
import unittest


@test_target("django_fixtureboy.fixtureloader:FixtureDataIterator")
class Tests(unittest.TestCase):
    fixture = """\
<?xml version="1.0" encoding="utf-8"?>
<django-objects version="1.0">
  <object model="auth.user" pk="1">
    <field name="password" type="CharField">pbkdf2_sha256$12000$EkLKlFVhP29P$kwgA5TeHRximayKt70Q3ixXA0mH5s2CqA82nw73AFn0=</field>
    <field name="last_login" type="DateTimeField">2014-11-21T14:23:06.645681</field>
    <field name="is_superuser" type="BooleanField">True</field>
    <field name="username" type="CharField">admin</field>
    <field name="first_name" type="CharField"></field>
    <field name="last_name" type="CharField"></field>
    <field name="email" type="CharField"></field>
    <field name="is_staff" type="BooleanField">True</field>
    <field name="is_active" type="BooleanField">True</field>
    <field name="date_joined" type="DateTimeField">2014-10-30T14:49:57.460464</field>
    <field name="groups" to="auth.group" rel="ManyToManyRel"></field>
    <field name="user_permissions" to="auth.permission" rel="ManyToManyRel"></field>
  </object>
</django-objects>
"""

    def test_it(self):
        from django_fixtureboy import Contract
        from django_fixtureboy.fixtureloader import XMLToDictHandler
        from django.contrib.auth.models import User
        contract = Contract()

        target = self._makeOne(self.fixture, contract, XMLToDictHandler)
        result = list(target)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], User)
        self.assertEqual(result[0][1], {
            'is_active': 'True',
            'first_name': '',
            'last_name': '',
            'username': 'admin',
            'id': '1',
            'password': 'pbkdf2_sha256$12000$EkLKlFVhP29P$kwgA5TeHRximayKt70Q3ixXA0mH5s2CqA82nw73AFn0=',
            'user_permissions': '',
            'date_joined': '2014-10-30T14:49:57.460464',
            'email': '',
            'is_staff': 'True',
            'is_superuser': 'True',
            'groups': '',
            'last_login': '2014-11-21T14:23:06.645681'
        })
