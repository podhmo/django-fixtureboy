# -*- coding:utf-8 -*-
from django_fixtureboy.testing import CleanHookTestCase
from evilunit import test_target


@test_target("django_fixtureboy:DefaultContract")
class Tests(CleanHookTestCase):
    def test_nohook(self):
        contract = self._makeOne()

        class Model:
            pass

        result = contract.name(Model)
        self.assertEqual(result, "ModelFactory")

    def test_with_hook(self):
        Contract = self._getTarget()

        @Contract.name.add_hook
        def hook(contract, gen, model):
            self.assertEqual(self.contract, contract)
            return "_" + gen()

        self.contract = self._makeOne()

        class Model:
            pass

        result = self.contract.name(Model)
        self.assertEqual(result, "_ModelFactory")

    def test_with_hook_multiples(self):
        Contract = self._getTarget()

        L = []

        @Contract.name.add_hook
        def hook0(contract, gen, model):
            L.append("b0")
            result = gen() + "0"
            L.append("a0")
            return result

        @Contract.name.add_hook
        def hook1(contract, gen, model):
            L.append("b1")
            result = gen() + "1"
            L.append("a1")
            return result

        @Contract.name.add_hook
        def hook2(contract, gen, model):
            L.append("b2")
            result = gen() + "2"
            L.append("a2")
            return result

        @Contract.name.add_hook
        def hook3(contract, gen, model):
            L.append("b3")
            result = gen() + "3"
            L.append("a3")
            return result

        self.contract = self._makeOne()

        class Model:
            pass

        result = self.contract.name(Model)
        self.assertEqual(result, "ModelFactory0123")
        self.assertEqual(L, ['b3', 'b2', 'b1', 'b0', 'a0', 'a1', 'a2', 'a3'])

    def test_with_hook_interrupt(self):
        from django_fixtureboy import withhook
        Contract = self._getTarget()

        L = []

        class MyContract(Contract):
            @withhook
            def name(self, model):
                L.append("original")
                raise Exception("oops")

            @name.add_hook
            def hook(self, gen, model):
                L.append("wrap0")
                raise Exception("oops2")

            @name.add_hook
            def hook2(self, gen, model):
                L.append("wrap1")
                return "Foo"

        contract = MyContract()

        class Model:
            pass

        result = contract.name(Model)
        self.assertEqual(result, "Foo")
        self.assertEqual(L, ["wrap1"])
