"""Course views package."""

from now_lms.vistas.courses.base import (
    ROUTE_LIST_COUPONS,
    TEMPLATE_COUPON_CREATE,
    TEMPLATE_COUPON_EDIT,
    VISTA_ADMINISTRAR_CURSO,
    VISTA_CURSOS,
    course,
    markdown2html,
    _emitir_certificado,
)

# Register routes (side effects)
from now_lms.vistas.courses import enrollment as _enrollment  # noqa: F401
from now_lms.vistas.courses import coupons as _coupons  # noqa: F401

from now_lms.vistas.courses.enrollment import _crear_indice_avance_curso

__all__ = [
    "course",
    "VISTA_CURSOS",
    "VISTA_ADMINISTRAR_CURSO",
    "ROUTE_LIST_COUPONS",
    "TEMPLATE_COUPON_CREATE",
    "TEMPLATE_COUPON_EDIT",
    "markdown2html",
    "_emitir_certificado",
    "_crear_indice_avance_curso",
]
