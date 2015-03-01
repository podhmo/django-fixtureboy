# -*- coding:utf-8 -*-
import contextlib
from srcgen.python import PythonModule as Module


class PythonModule(Module):
    @contextlib.contextmanager
    def call(self, name, limit=100):
        r = []
        yield r
        args = ", ".join(r)
        if limit < len(args):
            self.stmt("{}({})", name, "\n    " + ",\n    ".join(r))
        else:
            self.stmt("{}({})", name, args)
