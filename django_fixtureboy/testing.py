import unittest


class CleanHookTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django_fixtureboy import clearall_hooks
        clearall_hooks()

    def tearDown(self):
        from django_fixtureboy import clearall_hooks
        clearall_hooks()
