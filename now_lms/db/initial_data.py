# Copyright 2022 - 2023 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contributors:
# - William José Moreno Reyes

"""Codigo para crear cursos iniciales.s"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from datetime import datetime, timedelta, time
from os import environ, path, makedirs
from shutil import copyfile

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from ulid import ULID

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import proteger_passwd
from now_lms.config import DIRECTORIO_ARCHIVOS, DIRECTORIO_BASE_ARCHIVOS_USUARIO
from now_lms.logs import log
from now_lms.db import (
    database,
    Curso,
    CursoSeccion,
    CursoRecurso,
    CursoRecursoDescargable,
    Usuario,
    Etiqueta,
    EtiquetaCurso,
    Categoria,
    CategoriaCurso,
    Programa,
    ProgramaCurso,
    Recurso,
    UsuarioGrupo,
)

# pylint: disable=E1101
# pylint: disable=R0915
# pylint: disable=R0914


def crear_etiquetas():
    """Crea etiquetas de demostración."""
    log.trace("Creando etiquetas de demostración.")
    etiqueta1 = Etiqueta(nombre="Python", color="#FFD43B")
    etiqueta2 = Etiqueta(nombre="Postgresql", color="#0064a5")
    etiqueta3 = Etiqueta(nombre="HTML", color="#cc3b03")
    etiqueta4 = Etiqueta(nombre="Learning", color="#f2b3c4")
    database.session.add(etiqueta1)
    database.session.add(etiqueta2)
    database.session.add(etiqueta3)
    database.session.add(etiqueta4)
    database.session.commit()


def crear_categorias():
    """Crea categorias de demostración."""
    log.trace("Creando categorias de demostración.")
    cat1 = Categoria(nombre="Learning", descripcion="Cursos sobre aprendizaje")
    cat2 = Categoria(nombre="Programing", descripcion="Cursos sobre programación")
    database.session.add(cat1)
    database.session.add(cat2)
    database.session.commit()


def copy_sample_pdf():
    """Crea un archivo PDF de ejemplo."""

    log.trace("Creando archivo PDF de prueba.")
    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "NOW_Learning_Management_System.pdf")
    directorio_destino = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "files", "resources")
    try:  # pragma: no cover
        makedirs(directorio_destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass
    destino = path.join(directorio_destino, "NOW_Learning_Management_System.pdf")
    try:  # pragma: no cover
        copyfile(origen, destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass


def copy_sample_audio():
    """Crea un archivo audio de ejemplo."""

    log.trace("Creando archivo de audio de prueba.")
    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "En-us-hello.ogg")
    directorio_destino = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "audio", "resources")
    try:
        makedirs(directorio_destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass
    destino = path.join(directorio_destino, "En-us-hello.ogg")
    try:
        copyfile(origen, destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass


def copy_sample_img():
    """Crea un archivo de imagen de ejemplo."""

    log.trace("Creando archivo de imagen de prueba.")
    origen = path.join(DIRECTORIO_ARCHIVOS, "icons", "logo", "logo_large.png")
    directorio_destino = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "images", "resources")
    try:
        makedirs(directorio_destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass
    destino = path.join(directorio_destino, "logo_large.png")
    try:
        copyfile(origen, destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass


def curse_logo(curso: str, image: str, program=False):
    """Crea un archivo de imagen de ejemplo."""

    log.trace("Estableciendo logo tipo de curso de demostración.")
    origen = path.join(DIRECTORIO_ARCHIVOS, "img", image)
    if program:
        directorio_destino = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "images", "program" + curso)
    else:
        directorio_destino = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "images", curso)

    try:
        makedirs(directorio_destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass
    destino = path.join(directorio_destino, "logo.jpg")
    try:
        copyfile(origen, destino)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass


demo_external_code = """
    <iframe src="//www.slideshare.net/slideshow/embed_code/key/3gxt7XbHFmPBWP"
    width="595"
    height="485"
    frameborder="0"
    marginwidth="0"
    marginheight="0"
    scrolling="no"
    style="border:1px solid #CCC; border-width:1px; margin-bottom:5px;
    max-width: 100%;"
    allowfullscreen>
    </iframe>
    """


def crear_curso_demo():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creando curso de demo de recursos.")
    demo = Curso(
        nombre="Demo Course",
        codigo="resources",
        descripcion="This course will let you learn resource types.",
        estado="open",
        certificado=False,
        publico=True,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        promocionado=True,
        fecha_promocionado=datetime.today(),
    )

    database.session.add(demo)
    database.session.commit()
    curse_logo("resources", "11372802.jpg")

    ramdon1 = ULID()
    seccion_id = str(ramdon1)
    nueva_seccion = CursoSeccion(
        id=seccion_id,
        curso="resources",
        nombre="Demo of type of resources.",
        descripcion="Demo of type of resources.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion)
    database.session.commit()

    copy_sample_audio()
    nuevo_recurso6 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="mp3",
        nombre="A demo audio resource.",
        descripcion="Audio is easy to produce that videos.",
        base_doc_url="audio",
        doc="resources/En-us-hello.ogg",
        indice=1,
        publico=True,
    )
    database.session.add(nuevo_recurso6)
    database.session.commit()

    copy_sample_pdf()
    nuevo_recurso5 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="pdf",
        nombre="Demo pdf resource.",
        descripcion="A exampel of a PDF file to share with yours learners.",
        base_doc_url="files",
        doc="resources/NOW_Learning_Management_System.pdf",
        indice=2,
        publico=True,
    )
    database.session.add(nuevo_recurso5)
    database.session.commit()

    nuevo_recurso3 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="meet",
        nombre="A live meet about course sales.",
        descripcion="Live meets will improve your course.",
        url="https://en.wikipedia.org/wiki/Web_conferencing",
        indice=3,
        fecha=datetime.today() + timedelta(days=9),
        hora_inicio=time(hour=14, minute=30),
        hora_fin=time(hour=15, minute=00),
        notes="Google Meet",
        publico=False,
        requerido=2,
    )
    database.session.add(nuevo_recurso3)
    database.session.commit()

    copy_sample_img()
    nuevo_recurso4 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="img",
        nombre="A demo image file.",
        descripcion="A image file.",
        indice=4,
        publico=True,
        requerido=3,
        base_doc_url="images",
        doc="resources/logo_large.png",
    )
    database.session.add(nuevo_recurso4)
    database.session.commit()

    nuevo_recurso5 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="text",
        nombre="A demo text resource.",
        descripcion="A text in markdown.",
        indice=5,
        publico=False,
        requerido=3,
        text="# NOW - Learning Management System.",
    )
    database.session.add(nuevo_recurso5)
    database.session.commit()

    nuevo_recurso6 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="html",
        nombre="A demo external resouce resource.",
        descripcion="A HTML text.",
        indice=6,
        publico=False,
        external_code=demo_external_code,
    )
    database.session.add(nuevo_recurso6)
    database.session.commit()

    nuevo_recurso7 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="link",
        nombre="A external link.",
        descripcion="A external link.",
        indice=7,
        publico=False,
        url="https://es.wikipedia.org/wiki/Wikipedia:Portada",
    )
    database.session.add(nuevo_recurso7)
    database.session.commit()

    nuevo_recurso8 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="slides",
        nombre="A demo Slide Show.",
        descripcion="A demo Slide Show.",
        indice=8,
        publico=False,
    )
    database.session.add(nuevo_recurso8)
    database.session.commit()

    nuevo_recurso9 = CursoRecurso(
        curso="resources",
        seccion=seccion_id,
        tipo="youtube",
        nombre="A demo youtube video.",
        descripcion="A demo youtube video..",
        url="https://www.youtube.com/watch?v=TWQFHRt3dNg",
        indice=9,
        publico=False,
        requerido=2,
    )
    database.session.add(nuevo_recurso9)
    database.session.commit()

    log.debug("Curso de demo de recursos creado correctamente.")


def crear_curso_predeterminado():
    # pylint: disable=too-many-locals
    """Crea un recurso publico."""
    log.trace("Creando curso de demostración.")
    demo = Curso(
        nombre="OnLine Teaching 101",
        codigo="now",
        descripcion="Welcome! This is your first course.",
        estado="open",
        certificado=True,
        publico=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        duracion=7,
        nivel=1,
        precio=10,
        capacidad=50,
        auditable=True,
        portada=True,
        promocionado=True,
        fecha_promocionado=datetime.today(),
    )
    database.session.add(demo)
    database.session.commit()
    curse_logo("now", "5218255.jpg")

    ramdon1 = ULID()
    seccion1_id = str(ramdon1)
    nueva_seccion1 = CursoSeccion(
        id=seccion1_id,
        curso="now",
        nombre="Introduction to online teaching.",
        descripcion="This is introductory material to online teaching.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion1)
    database.session.commit()

    ramdon2 = ULID()
    seccion2_id = str(ramdon2)
    nueva_seccion2 = CursoSeccion(
        id=seccion2_id,
        curso="now",
        nombre="How to sell a online course.",
        descripcion="This is introductory material to how to sell your online course.",
        estado=False,
        indice=2,
    )

    database.session.add(nueva_seccion2)
    database.session.commit()

    nuevo_recurso1 = CursoRecurso(
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="Introduction to Online Teaching",
        descripcion="UofSC Center for Teaching Excellence - Introduction to Online Teaching.",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=1,
        publico=True,
    )
    database.session.add(nuevo_recurso1)
    database.session.commit()

    nuevo_recurso2 = CursoRecurso(
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="How to Teach OnLine.",
        descripcion="Kristina Garcia - Top Tips for New Online Teachers!",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=2,
        publico=False,
    )
    database.session.add(nuevo_recurso2)
    database.session.commit()

    nuevo_recurso2 = CursoRecurso(
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="What You Should Know BEFORE Becoming an Online English Teacher.",
        descripcion="Danie Jay - What You Should Know BEFORE Becoming an Online English Teacher | 10 Things I WISH I Knew",
        url="https://www.youtube.com/watch?v=9JBDSzSARHA",
        indice=2,
        publico=False,
    )
    database.session.add(nuevo_recurso2)
    database.session.commit()

    nuevo_recurso3 = CursoRecurso(
        curso="now",
        seccion=seccion2_id,
        tipo="youtube",
        nombre="4 Steps to Sell your Online Course with 0 audience.",
        descripcion="Sunny Lenarduzzi - No audience? No problem! YOU DON’T NEED AN AUDIENCE TO START A BUSINESS.",
        url="https://www.youtube.com/watch?v=TWQFHRt3dNg",
        indice=1,
        publico=False,
    )
    database.session.add(nuevo_recurso3)
    database.session.commit()

    log.debug("Curso de demostración creado correctamente.")


ADMIN = environ.get("ADMIN_USER") or environ.get("LMS_USER") or "lms-admin"
PASSWD = environ.get("ADMIN_PSWD") or environ.get("LMS_PSWD") or "lms-admin"


def crear_usuarios_predeterminados(with_examples):
    """Crea en la base de datos los usuarios iniciales."""
    log.info("Creando usuario administrador.")
    administrador = Usuario(
        usuario=ADMIN,
        acceso=proteger_passwd(PASSWD),
        nombre="System",
        apellido="Administrator",
        tipo="admin",
        activo=True,
        correo_electronico_verificado=True,
    )
    database.session.add(administrador)
    database.session.commit()
    log.debug("Usuario administrador creado correctamente.")

    if environ.get("CI") or with_examples:
        log.trace("Creando usuarios de demostración.")
        student = Usuario(
            usuario="student",
            acceso=proteger_passwd("student"),
            nombre="Meylin",
            apellido="Perez",
            correo_electronico="hello@domain.net",
            tipo="student",
            activo=True,
            visible=True,
            titulo=None,
            genero="female",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="Hello there!",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        student1 = Usuario(
            usuario="student1",
            acceso=proteger_passwd("student1"),
            nombre="Dania",
            apellido="Mendez",
            correo_electronico="hello1@domain.net",
            tipo="student",
            activo=True,
            visible=False,
            titulo=None,
            genero="female",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="Hello there!",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        student2 = Usuario(
            usuario="student2",
            acceso=proteger_passwd("student1"),
            nombre="Gema",
            apellido="Lopez",
            correo_electronico="hello3@domain.net",
            tipo="student",
            activo=True,
            visible=True,
            titulo=None,
            genero="female",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="Hello there!",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        student3 = Usuario(
            usuario="student3",
            acceso=proteger_passwd("student3"),
            nombre="Maria",
            apellido="Lopez",
            correo_electronico="hi@domain.com",
            tipo="student",
            activo=False,
            visible=False,
            titulo=None,
            genero="female",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="Hello there!",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        database.session.add(student)
        database.session.add(student1)
        database.session.add(student2)
        database.session.add(student3)
        demo_grupo1 = UsuarioGrupo(nombre="Usuarios Base", descripcion="Demo Group", activo=True)
        demo_grupo2 = UsuarioGrupo(nombre="Usuarios", descripcion="Demo Group", activo=True)
        database.session.add(demo_grupo2)
        database.session.add(demo_grupo1)
        database.session.commit()
        instructor = Usuario(
            usuario="instructor",
            acceso=proteger_passwd("instructor"),
            nombre="Nemesio",
            apellido="Reyes",
            correo_electronico="hello2@domain.net",
            tipo="instructor",
            activo=True,
            visible=False,
            genero="male",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="You can",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        database.session.add(instructor)
        database.session.commit()
        moderator = Usuario(
            usuario="moderator",
            acceso=proteger_passwd("moderator"),
            tipo="moderator",
            nombre="Abner",
            apellido="Romero",
            correo_electronico="moderator@mail.com",
            activo=True,
            visible=False,
            genero="male",
            nacimiento=datetime(year=1988, month=9, day=21),
            bio="You can do it.",
            url="google.com",
            linkedin="user",
            facebook="user",
            twitter="user",
            github="user",
        )
        database.session.add(moderator)
        database.session.commit()
        log.debug("Usuarios creados correctamente.")


def crear_curso_demo1():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creando curso de demostración PostgreSQL.")
    demo = Curso(
        nombre="PostgreSQL",
        codigo="postgresql",
        descripcion="This is a course about PostgreSQL.",
        estado="open",
        certificado=False,
        publico=True,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        promocionado=True,
        fecha_promocionado=datetime.today(),
    )

    database.session.add(demo)
    database.session.commit()
    curse_logo("postgresql", "999454.jpg")


def crear_curso_demo2():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creando curso de demostración Python.")
    demo = Curso(
        nombre="Python",
        codigo="python",
        descripcion="This is a course about Python.",
        estado="open",
        certificado=False,
        publico=True,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        promocionado=True,
        fecha_promocionado=datetime.today(),
    )

    database.session.add(demo)
    database.session.commit()
    curse_logo("python", "experiencia-programacion-persona-que-trabaja-codigos-computadora.jpg")


def crear_curso_demo3():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creando curso de demostración HTML.")
    demo = Curso(
        nombre="HTML",
        codigo="html",
        descripcion="This is a course about HTML.",
        estado="open",
        certificado=False,
        publico=True,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
    )

    database.session.add(demo)
    database.session.commit()
    curse_logo("html", "collage-fondo-programacion.jpg")


def asignar_cursos_a_etiquetas():
    """Asigna cursos a Categorias."""
    log.trace("Asignando etiquetas a cursos.")
    etiqueta_python = Etiqueta.query.filter(Etiqueta.nombre == "Python").first()
    etiqueta_postgresql = Etiqueta.query.filter(Etiqueta.nombre == "Postgresql").first()
    etiqueta_html = Etiqueta.query.filter(Etiqueta.nombre == "HTML").first()
    etiqueta_learning = Etiqueta.query.filter(Etiqueta.nombre == "Learning").first()

    registro1 = EtiquetaCurso(curso="postgresql", etiqueta=etiqueta_postgresql.id)
    registro2 = EtiquetaCurso(curso="python", etiqueta=etiqueta_python.id)
    registro3 = EtiquetaCurso(curso="html", etiqueta=etiqueta_html.id)
    registro4 = EtiquetaCurso(curso="now", etiqueta=etiqueta_learning.id)
    registro5 = EtiquetaCurso(curso="resources", etiqueta=etiqueta_learning.id)

    database.session.add(registro1)
    database.session.add(registro2)
    database.session.add(registro3)
    database.session.add(registro4)
    database.session.add(registro5)
    database.session.commit()


def asignar_cursos_a_categoria():
    """Asigna cursos a Categorias."""
    categoria_learning = Categoria.query.filter(Categoria.nombre == "Learning").first()
    categoria_programing = Categoria.query.filter(Categoria.nombre == "Programing").first()

    registro1 = CategoriaCurso(curso="postgresql", categoria=categoria_programing.id)
    registro2 = CategoriaCurso(curso="python", categoria=categoria_programing.id)
    registro3 = CategoriaCurso(curso="html", categoria=categoria_programing.id)
    registro4 = CategoriaCurso(curso="now", categoria=categoria_learning.id)
    registro5 = CategoriaCurso(curso="resources", categoria=categoria_learning.id)

    database.session.add(registro1)
    database.session.add(registro2)
    database.session.add(registro3)
    database.session.add(registro4)
    database.session.add(registro5)
    database.session.commit()


TEXTO_PROGRAMA = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident,
sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium
doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore
veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim
ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia
consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque
porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur,
adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et
dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum
exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi
consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse
quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas
nulla pariatur?
"""


def crear_programa():
    """Crea programa de pruebas."""

    programa = Programa(
        nombre="Programing 101",
        codigo="P001",
        descripcion="Introduction to programing",
        precio=100,
        publico=True,
        estado="open",
        logo=True,
        texto=TEXTO_PROGRAMA,
        promocionado=True,
        fecha_promocionado=datetime.today(),
    )
    curse_logo(curso="P001", image="concepto-collage-html-css-persona.jpg", program=True)
    database.session.add(programa)
    database.session.commit()

    # Asigna cursos a programa
    programa = Programa.query.filter(Programa.codigo == "P001").first()
    for curso in ["postgresql", "python", "html"]:
        curso = Curso.query.filter(Curso.codigo == curso).first()
        registro = ProgramaCurso(
            curso=curso.codigo,
            programa=programa.codigo,
        )
        database.session.add(registro)
        database.session.commit()


def crear_recurso_descargable():
    """Recurso descargable de ejemplo."""

    recurso1 = Recurso(
        nombre="Romeo and Juliet",
        codigo="R001",
        descripcion="Romeo and Juliet by William Shakespeare",
        precio=1,
        publico=True,
        logo=True,
        file_name="R001.pdf",
        tipo="ebook",
    )
    recurso2 = Recurso(
        nombre="Alice's Adventures in Wonderland",
        codigo="R002",
        descripcion="Alice's Adventures in Wonderland by Lewis Carroll.",
        precio=0,
        publico=True,
        logo=True,
        file_name="R002.pdf",
        tipo="ebook",
    )
    recurso3 = Recurso(
        nombre="Dracula",
        codigo="R003",
        descripcion="Dracula by Bram Stoker",
        precio=0,
        publico=True,
        logo=True,
        file_name="R003.pdf",
        tipo="ebook",
    )
    recurso4 = Recurso(
        nombre="The War of the Worlds",
        codigo="R004",
        descripcion="The War of the Worlds by H. G. Wells",
        precio=0,
        publico=True,
        logo=True,
        file_name="R004.pdf",
        tipo="ebook",
    )
    recurso4 = Recurso(
        nombre="Think Python",
        codigo="R005",
        descripcion="How to Think Like a Computer Scientist",
        precio=0,
        publico=True,
        logo=True,
        file_name="R005.pdf",
        tipo="ebook",
    )
    database.session.add(recurso1)
    database.session.add(recurso2)
    database.session.add(recurso3)
    database.session.add(recurso4)
    database.session.commit()

    directorio_destino_archivo = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "files", "resources_files")
    directorio_destino_imagen = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "images", "resources_files")
    try:  # pragma: no cover
        makedirs(directorio_destino_archivo)
        makedirs(directorio_destino_imagen)
    except FileExistsError:  # pragma: no cover
        pass
    except FileNotFoundError:  # pragma: no cover
        pass

    # Copiar pdf de ejemplo.
    archivos = [
        ("Romeo and Juliet by William Shakespeare.pdf", "R001.pdf"),
        ("Alice's Adventures in Wonderland by Lewis Carroll.pdf", "R002.pdf"),
        ("Dracula by Bram Stoker.pdf", "R003.pdf"),
        ("The War of the Worlds by H. G. Wells.pdf", "R004.pdf"),
        ("thinkpython2.pdf", "R005.pdf"),
    ]
    for archivo in archivos:
        origen = path.join(DIRECTORIO_ARCHIVOS, "examples", archivo[0])
        destino = path.join(directorio_destino_archivo, archivo[1])
        try:  # pragma: no cover
            copyfile(origen, destino)
        except FileExistsError:  # pragma: no cover
            pass
        except FileNotFoundError:  # pragma: no cover
            pass

    # Copiar img de ejemplo.
    imagenes = [
        ("Romeo_y_Julieta.jpg", "R001.jpg"),
        ("Alice's Adventures in Wonderland by Lewis Carroll.jpg", "R002.jpg"),
        ("Dracula by Bram Stoker.jpg", "R003.jpg"),
        ("The War of the Worlds by H. G. Wells.jpg", "R004.jpg"),
        ("thinkpython2.jpg", "R005.jpg"),
    ]
    for image in imagenes:
        origen = path.join(DIRECTORIO_ARCHIVOS, "examples", image[0])
        destino = path.join(directorio_destino_imagen, image[1])
        try:  # pragma: no cover
            copyfile(origen, destino)
        except FileExistsError:  # pragma: no cover
            pass
        except FileNotFoundError:  # pragma: no cover
            pass

    recurso = CursoRecursoDescargable(curso="now", recurso="R005")
    database.session.add(recurso)
    database.session.commit()
