"""Explicit identities for the first frozen financial reasoning supplement."""
import workflow_hard_borrowing_base
import workflow_hard_acquisition
import workflow_hard_receivables
import workflow_hard_waterfall

MODULES = {'a01':workflow_hard_borrowing_base,'b01':workflow_hard_acquisition,
           'c01':workflow_hard_receivables,'b02':workflow_hard_waterfall}


def specifications():
    return {key:module.specification() for key,module in MODULES.items()}


def controls(key, data):
    return MODULES[key].controls(data)


def alternatives(key):
    return MODULES[key].alternatives()


def mistakes(key):
    return MODULES[key].mistakes()
