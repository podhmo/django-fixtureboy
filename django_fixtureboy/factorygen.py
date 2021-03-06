from .langhelpers import PythonModule


class FactoryGenerator(object):
    def __init__(self, contract):
        self.models = contract.models
        self.contract = contract
        self.parts = [self.contract.initial_parts]

    def collect_parts(self):
        for m in self.models:
            self.parts.append(self.contract.parts(m))

    def generate(self, m=None):
        self.collect_parts()
        m = m or PythonModule()

        for parts in self.parts:
            for target in parts.lib:
                m.from_(target.__module__, target.__name__)
        m.sep()

        for parts in self.parts:
            if parts.name is None:
                continue
            with m.class_(parts.name, bases=parts.bases):
                for attr in parts.attrs:
                    if callable(attr):
                        attr(m)
                    else:
                        m.stmt(attr)

                m.sep()

                self.contract.gen_meta(m, parts)
        return self.contract.finish(m)
