# -*- coding:utf-8 -*-
from factory import SubFactory
from django.db.models.fields import NOT_PROVIDED


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


def _detect_choice_name(model, field, choices):
    choice_name = getattr(model, field.name, None)
    if choice_name is not None:
        return choice_name
    for k, v in model.__dict__.items():
        if v == choices:
            return k
    return None


def attrs_add_modelutils_choices_hook(contract, gen, model):
    """
    # in model
    COLOR = Choices(("red", "r", 1), ("green", "g", 2), ("blue", "b", 3))
    color = models.IntegerField(choices=COLOR)

    # then
    color = Model.Color.red  # red
    """
    from model_utils import Choices

    attrs = gen()
    for f in model._meta.local_fields:
        if f.choices:
            if isinstance(f.choices, Choices):
                choice_name = _detect_choice_name(model, f, f.choices)
                if choice_name is not None:
                    value, attrname, label = f.choices._triples[0]
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
                    continue

            if isinstance(f.choices, (list, tuple)):
                if f.default is NOT_PROVIDED:
                    value = f.choices[0]
                else:
                    value = f.default
                attrs.append("{name} = {value!r}".format(name=f.name, value=value))
    return attrs


def finish_add_autopep8_hook(contract, gen, m):
    from autopep8 import fix_code
    code = gen()
    return fix_code(code, encoding="utf-8")
