"""Explicit identities for the second experimental development catalog."""
import workflow_hard_covenant
import workflow_hard_convertibles

MODULES = {'a01':workflow_hard_covenant,'b01':workflow_hard_convertibles}


def specifications():
    return {key:module.specification() for key,module in MODULES.items()}


def controls(key, data):
    return MODULES[key].controls(data)


def alternatives(key):
    return MODULES[key].alternatives()


def mistakes(key):
    return MODULES[key].mistakes()
