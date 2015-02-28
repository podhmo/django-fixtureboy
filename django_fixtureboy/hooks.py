# -*- coding:utf-8 -*-
from factory import SubFactory
from model_utils import Choices


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


def attrs_add_modelutils_choices_hook(contract, gen, model):
    """
    # in model
    COLOR = Choices(("red", "r", 1), ("green", "g", 2), ("blue", "b", 3))
    color = models.IntegerField(choices=COLOR)

    # then
    color = Model.Color.red
    """
    attrs = gen()
    for f in model._meta.local_fields:
        choice_name = f.name.upper()
        choices = getattr(model, choice_name, None)
        if choices is not None:
            value, attrname, label = choices._triples[0]
            kwargs = {"name": f.name,
                      "model": model.__name__,
                      "choice": choice_name,
                      "attrname": attrname,
                      "value": value,
                      "label": label}
            if value == attrname:
                attrs.append("{name} = {value!r}  # {label}".format(**kwargs))
            else:
                attrs.append("{name} = {model}.{choice}.{attrname}  # {label}".format(**kwargs))
    return attrs
