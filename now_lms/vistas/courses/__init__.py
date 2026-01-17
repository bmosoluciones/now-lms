"""Course views package."""

from now_lms.vistas.courses.base import (
    ROUTE_LIST_COUPONS,
    TEMPLATE_COUPON_CREATE,
    TEMPLATE_COUPON_EDIT,
    VISTA_ADMINISTRAR_CURSO,
    VISTA_CURSOS,
    course,
)
from now_lms.vistas.courses.helpers import markdown2html, _crear_indice_avance_curso, _emitir_certificado

# Register routes (side effects)
from now_lms.vistas.courses import enrollment as _enrollment  # noqa: F401
from now_lms.vistas.courses import coupons as _coupons  # noqa: F401
from now_lms.vistas.courses import actions as _actions  # noqa: F401
from now_lms.vistas.courses import resources as _resources  # noqa: F401

__all__ = [
    "course",
    "_resources",
    "VISTA_CURSOS",
    "VISTA_ADMINISTRAR_CURSO",
    "ROUTE_LIST_COUPONS",
    "TEMPLATE_COUPON_CREATE",
    "TEMPLATE_COUPON_EDIT",
    "markdown2html",
    "_crear_indice_avance_curso",
    "_emitir_certificado",
]
