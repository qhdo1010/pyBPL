"""
Generate character
"""

from __future__ import print_function, division

from pybpl.classes import MotorProgram, CPD
from pybpl.generate_exemplar import generate_exemplar
from pybpl.parameters import defaultps


def generate_character(libclass, ns=None):
    if ns is None:
        numstrokes = CPD.sample_number(libclass)
        ns = numstrokes.data[0]
    template = MotorProgram(ns)
    template.parameters = defaultps()
    print('ns: %i' % ns)
    # for each stroke, sample its template
    for i in range(ns):
        # this needs to be checked
        template.S[i].R = CPD.sample_relation_type(libclass, template.S[0:i])
        template.S[i].ids = CPD.sample_sequence(libclass, ns)
        template.S[i].shapes_type = CPD.sample_shape_type(
            libclass, template.S[i].ids
        )
        template.S[i].invscales_type = CPD.sample_invscales_type(
            libclass, template.S[i].ids
        )
    return template, lambda: generate_exemplar(template, libclass)