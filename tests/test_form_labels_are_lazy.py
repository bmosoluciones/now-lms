# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Form labels must be lazily translated.

``now_lms/i18n.py`` documents the rule:

    # Para traducciones perezosas (formularios):
    # from now_lms.i18n import _l
    # field = StringField(_l('Etiqueta del campo'))

A class-body ``_()`` call is evaluated when the module is imported — before any
request exists — so the label freezes to whichever locale happened to be active
at import time and never changes again. ``_l()`` defers resolution to render
time, which is what makes a form translate per request.

This test walks every WTForms class in ``now_lms.forms`` and asserts the labels
are lazy, so the convention cannot silently regress.
"""

from __future__ import annotations

import inspect

from flask_babel import LazyString
from flask_wtf import FlaskForm

import now_lms.forms as forms_module


# A label supplied positionally to a Field becomes field.kwargs["label"] on the
# UnboundField; WTForms falls back to a prettified attribute name when no label
# was given, and those are plain strings we must not flag.
def _explicit_labels():
    """Yield (form_name, field_name, label) for every explicitly-labelled field."""
    for form_name, form_class in vars(forms_module).items():
        if not (inspect.isclass(form_class) and issubclass(form_class, FlaskForm) and form_class is not FlaskForm):
            continue
        if form_class.__module__ != forms_module.__name__:
            continue
        for field_name in dir(form_class):
            unbound = getattr(form_class, field_name, None)
            if not hasattr(unbound, "field_class"):
                continue
            label = unbound.kwargs.get("label")
            if label is None and unbound.args:
                label = unbound.args[0]
            if label is None:
                continue
            yield form_name, field_name, label


def test_at_least_one_labelled_field_is_discovered():
    """Guard the walker itself — a silent zero would make this test vacuous."""
    assert len(list(_explicit_labels())) > 50


def test_every_form_label_is_lazily_translated():
    """No class-body label may be an eagerly-translated plain string."""
    eager = [
        f"{form_name}.{field_name} = {label!r}"
        for form_name, field_name, label in _explicit_labels()
        if isinstance(label, str) and not isinstance(label, LazyString)
    ]
    assert not eager, "these labels are evaluated at import time; use _l() instead of _():\n  " + "\n  ".join(eager)
