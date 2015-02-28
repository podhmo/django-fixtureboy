# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from functools import partial
from collections import defaultdict
import pkg_resources
dummy = object()


def import_symbol(symbol):
    return pkg_resources.EntryPoint.parse("x=%s" % symbol).load(False)


class HookPoint(object):
    def __init__(self, method):
        self.hooks = defaultdict(list)
        self.method = method
        self.cls = dummy
        self.name = None

    def __get__(self, ob, type_):
        if ob is None:
            self.cls = type_
            return self
        fn = partial(self.method, ob)
        if not self.hooks[type_]:
            return fn

        def wrapped(*args, **kwargs):
            gen = partial(fn, *args, **kwargs)
            for hook in self.hooks[type_]:
                gen = partial(hook, ob, gen, *args, **kwargs)
            return gen()
        return wrapped

    def get_callable(self, hook):
        if callable(hook):
            return hook
        return import_symbol(hook)

    def add_hook(self, hook):
        hook = self.get_callable(hook)
        if hook in self.hooks[self.cls]:
            return
        logger.debug("add hook: name=%s, cls=%s, hook=%s", self.name, self.cls, hook)
        self.hooks[self.cls].append(hook)
        return hook

    def remove_hook(self, hook):
        hook = self.get_callable(hook)
        logger.debug("remove hook: name=%s, cls=%s, hook=%s", self.name, self.cls, hook)
        self.hooks[self.cls].remove(hook)

    def clear(self):
        for cls, hooks in self.hooks.items():
            logger.debug("clear hooks: name=%s, cls=%s", self.name, cls)
            hooks.clear()

    def apply_dummy(self, cls):
        val = self.hooks.pop(dummy, None)
        if val is not None:
            logger.debug("move hooks: name=%s, dummy -> cls=%s", self.name, cls)
            self.hooks[cls].extend(val)


class HookPointFactory(object):
    def __init__(self):
        self.hookpoints = []

    def __call__(self, method):
        hookpoint = HookPoint(method)
        self.hookpoints.append(hookpoint)
        return hookpoint

    def clearall(self):
        for hookpoint in self.hookpoints:
            hookpoint.clear()


# xxx:
withhook = HookPointFactory()
clearall_hooks = withhook.clearall


class HasHookPointMeta(type):
    def __new__(self, name, bases, attrs):
        cls = super(HasHookPointMeta, self).__new__(self, name, bases, attrs)
        for k, v in attrs.items():
            if isinstance(v, HookPoint):
                v.apply_dummy(cls)
                v.name = k
        return cls
