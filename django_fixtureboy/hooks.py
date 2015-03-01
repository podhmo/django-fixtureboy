# -*- coding:utf-8 -*-
from factory import SubFactory, post_generation
from django.db.models.fields import NOT_PROVIDED
from functools import partial
from collections import defaultdict
from .codegen import eager, ReprWrapper


def attrs_add_subfactory_hook(contract, gen, model):
    attrs = gen()
    contract.initial_parts.lib.add(contract.build_import_sentence(SubFactory))
    # contract.initial_parts.lib.add(contract.build_import_sentence(RelatedFactoy))

    for f in model._meta.local_fields:
        if f.rel is not None:
            relmodel = f.rel.to.__name__
            attrs.append("{name} = SubFactory({model})".format(name=f.name, model=relmodel))
    return attrs


def attrs_add_many_to_many_post_generation_hook(contract, gen, model):
    attrs = gen()
    if not model._meta.local_many_to_many:
        return attrs
    contract.initial_parts.lib.add(contract.build_import_sentence(post_generation))

    for f in model._meta.local_many_to_many:
        def generate_code_with_srcgen(m, f=f):
            m.stmt("@post_generation")
            with m.def_(f.name, "create", "extracted", "**kwargs"):
                with m.if_("not create"):
                    m.return_("")

                with m.if_("extracted"):
                    with m.for_("x", "extracted"):
                        m.stmt("self.{}.add(x)".format(f.name))
        attrs.append(generate_code_with_srcgen)
    return attrs


class _ChoicesInfoDetector(object):
    name_map = defaultdict(dict)  # model -> field.name -> choice_name
    reverse_identifier_map = defaultdict(dict)  # model -> value -> identifier

    @classmethod
    def choice_name(cls, model, field):
        r = cls.name_map[model].get(field.name)
        if r is not None:
            return r

        gueesing = field.name.upper()
        choice_name = getattr(model, gueesing, None)
        if choice_name is not None:
            cls.name_map[model][field.name] = gueesing
            return choice_name
        for name, attr in model.__dict__.items():
            if attr == field.choices:
                cls.name_map[model][field.name] = name
                return name
        return None

    @classmethod
    def choice_attr(cls, model, field, value):
        r = cls.reverse_identifier_map[model].get(value)
        if r is not None:
            return r
        identifier_map = field.choices._identifier_map
        D = cls.reverse_identifier_map[model] = {v: k for k, v in identifier_map.items()}
        return D[value]


def args_add_modelutils_choices_hook(contract, gen, model, field, value):
    choicename = _ChoicesInfoDetector.choice_name(model, field)
    if choicename is None:
        return value
    attrname = _ChoicesInfoDetector.choice_attr(model, field, value)
    return ReprWrapper("{}.{}.{}".format(model.__name__, choicename, attrname))


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
                choice_name = _ChoicesInfoDetector.choice_name(model, f)
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


# codegen
def setup_add_jsonfield_hook(contract, gen, emitter):
    from jsonfield import JSONField
    emitter.alias_map[JSONField.__name__] = eager(partial(JSONField.to_python, None))
