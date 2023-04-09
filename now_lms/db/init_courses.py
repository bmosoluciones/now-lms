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

# pylint: disable=E1101
# pylint: disable=R0915

# Libreria standar:
from datetime import datetime, timedelta, time
from os import environ

# Librerias de terceros:
from loguru import logger as log
from ulid import ULID

# Recursos locales:
from now_lms.auth import proteger_passwd
from now_lms.db import database, Curso, CursoSeccion, CursoRecurso, Usuario


def copy_sample_pdf():
    """Crea un archivo PDF de ejemplo."""
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "NOW_Learning_Management_System.pdf")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "files", "resources")
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
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "En-us-hello.ogg")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "audio", "resources")
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
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "icons", "logo", "logo_large.png")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "images", "resources")
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


def curse_logo(curso: str):
    """Crea un archivo de imagen de ejemplo."""
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "img", "5218255.jpg")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "images", curso)
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
    log.info("Creando curso de demo de recursos.")
    demo = Curso(
        nombre="Demo Course",
        codigo="resources",
        descripcion="This course will let you learn resource types.",
        estado="draft",
        certificado=False,
        publico=False,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
    )
    database.session.add(demo)
    database.session.commit()
    curse_logo("resources")

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
    log.info("Creando curso de demostración.")
    demo = Curso(
        nombre="OnLine Learning 101",
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
    )
    database.session.add(demo)
    database.session.commit()
    curse_logo("now")

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

if ADMIN == "lms-admin" and PASSWD == "lms-admin":  # nosec B105
    log.warning("Utilizando usuario y contraseña predeterminada para el usuario administrador.")


def crear_usuarios_predeterminados():
    """Crea en la base de datos los usuarios iniciales."""
    log.info("Creando usuario administrador.")
    administrador = Usuario(
        usuario=ADMIN,
        acceso=proteger_passwd(PASSWD),
        nombre="System",
        apellido="Administrator",
        tipo="admin",
        activo=True,
    )
    database.session.add(administrador)
    database.session.commit()
    log.debug("Usuario administrador creado correctamente.")

    # Crea un usuario de cada perfil (admin, user, instructor, moderator)
    # por defecto desactivados.
    log.info("Creando usuarios de demostración.")
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
    database.session.add(student)
    database.session.add(student1)
    database.session.add(student2)
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
