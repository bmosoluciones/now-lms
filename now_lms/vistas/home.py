# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, redirect, render_template, request
from flask_login import current_user, login_required

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache, no_guardar_en_cache_global
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Curso, CursoRecurso, Usuario, database

home = Blueprint("home", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Página de inicio de la aplicación.
# ---------------------------------------------------------------------------------------
@home.route("/")
@home.route("/home")
@cache.cached(timeout=90, unless=no_guardar_en_cache_global)
def pagina_de_inicio():
    """Página principal de la aplicación."""

    if DESARROLLO:  # pragma: no cover
        MAX = 3
    else:  # pragma: no cover
        MAX = MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA

    CURSOS = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX,
        count=True,
    )

    return render_template("inicio/mooc.html", cursos=CURSOS)


@home.route("/home/panel")
@login_required
def panel():
    """Panel principal de la aplicacion luego de inicar sesión."""
    if not current_user.is_authenticated:
        return redirect("/home")
    elif current_user.tipo == "admin":
        cursos_actuales = Curso.query.count()
        usuarios_registrados = Usuario.query.count()
        recursos_creados = CursoRecurso.query.count()
        cursos_por_fecha = Curso.query.order_by(Curso.creado).limit(5).all()
        return render_template(
            "inicio/panel.html",
            cursos_actuales=cursos_actuales,
            usuarios_registrados=usuarios_registrados,
            recursos_creados=recursos_creados,
            cursos_por_fecha=cursos_por_fecha,
        )
    else:
        return redirect("/")
