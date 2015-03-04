# -*- coding:utf-8 -*-
from functools import partial
from prestring.python import PythonModule as _PythonModule


PythonModule = partial(_PythonModule, width=80)
