# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from factory import SubFactory, post_generation
from django.db.models.fields import NOT_PROVIDED
from functools import partial
from collections import defaultdict
from .codegen import eager, ReprWrapper


def attrs_add_subfactory_hook(contract, gen, model):
    attrs = gen()
    contract.initial_parts.lib.add(SubFactory)
    # contract.initial_parts.lib.add(RelatedFactoy)

    for f in model._meta.local_fields:
        if f.rel is not None:
            relmodel = f.rel.to.__name__
            attrs.append("{name} = SubFactory({model})".format(name=f.name, model=relmodel))
    return attrs


def attrs_add_many_to_many_post_generation_hook(contract, gen, model):
    attrs = gen()
    if not model._meta.local_many_to_many:
        return attrs
    contract.initial_parts.lib.add(post_generation)

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


class _ChoiceIdentifierNotfound(Exception):
    pass


class _ChoicesInfoDetector(object):
    name_map = defaultdict(dict)  # model -> field.name -> choice_name
    reverse_map = defaultdict(dict)  # model -> value -> identifier

    @classmethod
    def choice_name(cls, model, field):
        r = cls.name_map[model].get(field.name)
        if r is not None:
            return r

        gueesing = field.name.upper()
        choice_candidates = getattr(model, gueesing, None)
        if choice_candidates == field.choices:
            cls.name_map[model][field.name] = gueesing
            return gueesing
        for name, attr in model.__dict__.items():
            if attr == field.choices:
                cls.name_map[model][field.name] = name
                return name
        return None

    @classmethod
    def _get_from_submap(cls, submap, model, field, value):
        try:
            return submap[value]
        except KeyError:
            logger.warn("KeyError: model=%s, field=%s, value=%s", model, field, value)
            triple = field.choices._triples[0]
            if triple[1] == triple[0]:  # (value,  doc)
                raise _ChoiceIdentifierNotfound(triple[0])
            else:  # (value, identifier, doc)
                return triple[1]

    @classmethod
    def choice_attr(cls, model, field, value):
        submap = cls.reverse_map[model].get(field.name)
        if submap is not None:
            return cls._get_from_submap(submap, model, field, value)
        identifier_map = field.choices._identifier_map
        submap = {v: k for k, v in identifier_map.items()}
        cls.reverse_map[model][field.name] = submap
        return cls._get_from_submap(submap, model, field, value)


def args_add_modelutils_choices_hook(contract, gen, model, field, value):
    from model_utils import Choices
    value = gen()
    choicename = _ChoicesInfoDetector.choice_name(model, field)
    if choicename is None:
        return value
    if not isinstance(field.choices, Choices):
        return value
    try:
        attrname = _ChoicesInfoDetector.choice_attr(model, field, value)
    except _ChoiceIdentifierNotfound as e:
        return e.args[0]

    if str(attrname) == str(value):
        return value
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


class BuildDataOmmitingHook(object):
    def __init__(self, *keys):
        self.keys = keys

    def __call__(self, contract, gen, model, data):
        data = gen()
        for k in self.keys:
            data.pop(k, None)
        return data


def build_data_omitting_same_as_default(constract, gen, model, _):
    data = gen()
    for f in model._meta.local_fields:
        if f.default is NOT_PROVIDED:
            continue
        if f.rel is not None:
            continue
        if callable(f.default):
            continue
        if f.name in data and str(data[f.name]) == str(f.default):
            data.pop(f.name)
