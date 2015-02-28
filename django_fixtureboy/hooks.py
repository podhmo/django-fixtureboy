# -*- coding:utf-8 -*-
from factory import SubFactory


def attrs_add_subfactory_hook(contract, gen, model):
    brain = contract.brain
    attrs = gen()
    contract.initial_parts.lib.add(contract.build_import_sentence(SubFactory))
    # contract.initial_parts.lib.add(contract.build_import_sentence(RelatedFactoy))

    for f in model._meta.local_fields:
        if brain.is_foreinkey(f):
            relmodel = f.rel.to.__name__
            attrs.append("{name} = SubFactory({model})".format(name=f.name, model=relmodel))
    return attrs
