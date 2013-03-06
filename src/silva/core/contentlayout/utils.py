# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import types
from five import grok
from zope.interface import implementedBy
from zope.interface.interfaces import ISpecification


def verify_context(cls, obj, implements=False):
    require = None
    if isinstance(cls, (types.ClassType, type)):
        require = specification = grok.context.bind(default=None).get(cls)
        if require is None:
            return True, require
        if not ISpecification.providedBy(specification):
            specification = implementedBy(specification)
        if implements:
            if not specification.implementedBy(obj):
                return False, require
        else:
            if not specification.providedBy(obj):
                return False, require
    return True, require
