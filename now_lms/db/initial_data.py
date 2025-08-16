# Copyright 2022 - 2024 BMO Soluciones, S.A.
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

"""Codigo para crear cursos iniciales.s"""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, time, timedelta
from os import environ, listdir, makedirs, path
from shutil import copyfile, copytree
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from ulid import ULID

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import proteger_passwd
from now_lms.config import DIRECTORIO_ARCHIVOS, DIRECTORIO_BASE_ARCHIVOS_USUARIO
from now_lms.db import (
    Categoria,
    CategoriaCurso,
    Certificacion,
    Certificado,
    Curso,
    CursoRecurso,
    CursoRecursoDescargable,
    CursoSeccion,
    Etiqueta,
    EtiquetaCurso,
    Programa,
    ProgramaCurso,
    Recurso,
    SystemInfo,
    Usuario,
    database,
)
from now_lms.logs import log
from now_lms.version import MAYOR, MENOR, VERSION

# User constants
ADMIN_USER = environ.get("ADMIN_USER", None) or "lms-admin"
ADMIN_USER_WITH_FALLBACK = environ.get("ADMIN_USER") or environ.get("LMS_USER") or "lms-admin"

if TYPE_CHECKING:
    from flask import Flask


def system_info(app: "Flask"):
    """Información básica de la instalación."""

    with app.app_context():
        version_sistema = SystemInfo(param="version", val=VERSION)
        version_sistema_mayor = SystemInfo(param="version_mayor", val=str(MAYOR))
        version_sistema_menor = SystemInfo(param="version_menor", val=str(MENOR))

        database.session.add(version_sistema)
        database.session.add(version_sistema_menor)
        database.session.add(version_sistema_mayor)
        database.session.commit()


def crear_etiquetas():
    """Crea etiquetas de demostración."""
    log.trace("Creating demonstration tags.")
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
    log.trace("Creating demonstration categories.")
    cat1 = Categoria(nombre="Learning", descripcion="Cursos sobre aprendizaje")
    cat2 = Categoria(nombre="Programing", descripcion="Cursos sobre programación")
    database.session.add(cat1)
    database.session.add(cat2)
    database.session.commit()


def copy_sample_pdf():
    """Crea un archivo PDF de ejemplo."""

    log.trace("Creating test PDF file.")
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

    log.trace("Creating test audio file.")
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

    log.trace("Creating test image file.")
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

    log.trace("Setting demonstration course logo.")
    origen = path.join(str(DIRECTORIO_ARCHIVOS), "img", image)
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
    log.trace("Creating resource demo course.")
    demo = Curso(
        nombre="Demo Course",
        codigo="resources",
        descripcion_corta="Demo Course for resources types.",
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
        plantilla_certificado="horizontal",
    )

    database.session.add(demo)
    database.session.commit()
    curse_logo("resources", "11372802.jpg")
    curse_logo("details", "11372802.jpg")

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
        descripcion="Audio is easier to produce than videos.",
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

    log.debug("Resource demo course created successfully.")


# https://medium.com/printcss/printcss-create-your-certificate-pdfs-with-html-and-css-926e7dcf6281
HTML = """
<div class="border-pattern">
 <div class="content">
  <div class="inner-content">
   <h1>Certificate Testing</h1>
   <h2>Now Learning Management System</h2>
   <h3>congrats your lms setup can generate PDF files</h3>
   <div class="badge">
   </div>
  </div>
 </div>
</div>
"""

CSS = """
@page{
 size:A4 landscape;
 margin:10mm;
}
body{
 margin:0;
 padding:0;
 border:1mm solid #991B1B;
 height:188mm;
}

.border-pattern{
 position:absolute;
 left:4mm;
 top:-6mm;
 height:200mm;
 width:267mm;
 border:1mm solid #991B1B;
 /* http://www.heropatterns.com/ */
 background-color: #d6d6e4;
 background-image: url("data:image/svg+xml,%3Csvg width='16' height='16' viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h16v2h-6v6h6v8H8v-6H2v6H0V0zm4 4h2v2H4V4zm8 8h2v2h-2v-2zm-8 0h2v2H4v-2zm8-8h2v2h-2V4z' fill='%23991B1B' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.content{
 position:absolute;
 left:10mm;
 top:10mm;
 height:178mm;
 width:245mm;
 border:1mm solid #991B1B;
 background:white;
}

.inner-content{
 border:1mm solid #991B1B;
 margin:4mm;
 padding:10mm;
 height:148mm;
 text-align:center;
}

h1{
 text-transform:uppercase;
 font-size:48pt;
 margin-bottom:0;
}
h2{
 font-size:24pt;
 margin-top:0;
 padding-bottom:1mm;
 display:inline-block;
 border-bottom:1mm solid #991B1B;
}
h2::after{
 content:"";
 display:block;
 padding-bottom:4mm;
 border-bottom:1mm solid #991B1B;
}
h3{
 font-size:20pt;
 margin-bottom:0;
 margin-top:10mm;
}
p{
 font-size:16pt;
}

.badge{
 width:40mm;
 height:40mm;
 position:absolute;
 right:10mm;
 bottom:10mm;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z' /%3E%3C/svg%3E");
}
"""


def crear_certificados():
    """Crea un certificado de prueba."""
    log.trace("Creating demo certificate.")

    demo = Certificado(
        id="1234567890",
        html=HTML,
        css=CSS,
        titulo="Demo Certificado",
        descripcion="Puede verificar la generación de PDF con este certificado.",
        code="demo",
        habilitado=False,
        publico=False,
    )
    database.session.add(demo)
    database.session.commit()

    from now_lms.db.certificates_templates import CERTIFICADOS

    for certificado in CERTIFICADOS:
        cert = Certificado(
            titulo=certificado[0],
            descripcion=certificado[1],
            html=certificado[2],
            css=certificado[3],
            code=certificado[4],
            habilitado=True,
            publico=True,
        )
        database.session.add(cert)
        database.session.commit()


def crear_certificacion():
    certificacion = Certificacion(
        id="01JS2NK7NJ74DBSHD83MGRH5HE",
        usuario=ADMIN_USER_WITH_FALLBACK,
        curso="now",
        certificado="demo",
    )
    database.session.add(certificacion)
    database.session.commit()


def crear_curso_predeterminado():
    # pylint: disable=too-many-locals
    """Crea un recurso publico."""
    log.trace("Creating demonstration course.")
    demo = Curso(
        nombre="OnLine Teaching 101",
        codigo="now",
        descripcion_corta="This is your first course.",
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
    form = Curso(
        nombre="Course Details",
        codigo="details",
        descripcion_corta="This is a course details example.",
        descripcion="#Course Details Example",
        portada=True,
        nivel=2,
        duracion=40,
        # Estado de publicación
        estado="draft",
        publico=True,
        # Modalidad
        modalidad="time_based",
        # Disponibilidad de cupos
        limitado=True,
        capacidad=100,
        # Fechas de inicio y fin
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        # Información de marketing
        promocionado=True,
        fecha_promocionado=datetime.today(),
        # Información de pago
        pagado=True,
        auditable=True,
        precio=100,
        certificado=True,
        plantilla_certificado="horizontal",
    )
    free = Curso(
        nombre="Free Course",
        codigo="free",
        descripcion_corta="This is a free course.",
        descripcion="#Free demo course",
        portada=True,
        nivel=0,
        duracion=1,
        # Estado de publicación
        estado="open",
        publico=True,
        # Modalidad
        modalidad="self_paced",
        # Disponibilidad de cupos
        limitado=False,
        capacidad=0,
        # Fechas de inicio y fin
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        # Información de marketing
        promocionado=True,
        fecha_promocionado=datetime.today(),
        # Información de pago
        pagado=False,
        auditable=False,
        precio=0,
        certificado=True,
        plantilla_certificado="horizontal",
    )
    database.session.add(demo)
    database.session.add(form)
    database.session.add(free)
    database.session.commit()
    curse_logo("now", "5218255.jpg")
    curse_logo("details", "online-course.jpg")
    curse_logo("free", "manos-trabajando.jpg")

    seccion1_id = "01HPB1MZXBHZETC4ZH0HV4G39Q"
    nueva_seccion1 = CursoSeccion(
        id=seccion1_id,
        curso="now",
        nombre="Introduction to online teaching.",
        descripcion="This is introductory material to online teaching.",
        estado=False,
        indice=1,
    )

    seccion1a_id = "02HPB1MZXBHZETC4ZH0HV4G39A"
    nueva_seccion1a = CursoSeccion(
        id=seccion1a_id,
        curso="free",
        nombre="Welcome to your free course.",
        descripcion="Welcome to your free course.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion1)
    database.session.add(nueva_seccion1a)
    database.session.commit()

    seccion2_id = "01HPB1Q1R4HGJPG3C5NSFX3GH2"
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
        id="01HPB3AP3QNVK9ES6JGG5YK7CH",
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="Introduction to Online Teaching",
        descripcion="UofSC Center for Teaching Excellence - Introduction to Online Teaching.",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=1,
        publico=True,
    )
    nuevo_recurso1a = CursoRecurso(
        id="02HPB3AP3QNVK9ES6JGG5YK7CA",
        curso="free",
        seccion=seccion1a_id,
        tipo="youtube",
        nombre="The Evolution of Online Learning with Dhawal Shah",
        descripcion="Dhawal's journey into the world of online education is as inspiring as it is insightful.",
        url="https://www.youtube.com/watch?v=mMvRbZtqg5o",
        indice=1,
        publico=False,
    )
    database.session.add(nuevo_recurso1)
    database.session.add(nuevo_recurso1a)
    database.session.commit()

    nuevo_recurso2 = CursoRecurso(
        id="01HPB3BC71R8WFZXFS8BSH5QEG",
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
        id="01HPB3C1EDYAX5JWV49GXWNFJF",
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="What You Should Know BEFORE Becoming an Online English Teacher.",
        descripcion="Danie Jay - What You Should Know BEFORE Becoming an Online English Teacher | 10 Things I WISH I Knew",
        url="https://www.youtube.com/watch?v=9JBDSzSARHA",
        indice=3,
        publico=False,
    )
    database.session.add(nuevo_recurso2)
    database.session.commit()

    nuevo_recurso3 = CursoRecurso(
        id="01HPB3CGYV6PQXF4DXEEM3QT78",
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

    log.debug("Demonstration course created successfully.")


def crear_usuarios_predeterminados():
    """Crea en la base de datos los usuarios iniciales."""
    log.info("Creating administrator user.")
    administrador = Usuario(
        usuario=ADMIN_USER_WITH_FALLBACK,
        acceso=proteger_passwd(environ.get("ADMIN_PSWD") or environ.get("LMS_PSWD") or "lms-admin"),
        nombre="System",
        apellido="Administrator",
        tipo="admin",
        activo=True,
        correo_electronico_verificado=True,
    )
    database.session.add(administrador)
    database.session.commit()
    log.debug("Administrator user created successfully.")


def crear_curso_demo1():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creating PostgreSQL demonstration course.")
    demo = Curso(
        nombre="PostgreSQL",
        codigo="postgresql",
        descripcion_corta="A course about PostgreSQL.",
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
    log.trace("Creating Python demonstration course.")
    demo = Curso(
        nombre="Python",
        codigo="python",
        descripcion_corta="A course about Python.",
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
    log.trace("Creating HTML demonstration course.")
    demo = Curso(
        nombre="HTML",
        codigo="html",
        descripcion_corta="A course about HTML.",
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
    log.trace("Assigning tags to courses.")
    etiqueta_python = database.session.execute(
        database.select(Etiqueta).filter(Etiqueta.nombre == "Python")
    ).scalar_one_or_none()
    etiqueta_postgresql = database.session.execute(
        database.select(Etiqueta).filter(Etiqueta.nombre == "Postgresql")
    ).scalar_one_or_none()
    etiqueta_html = database.session.execute(database.select(Etiqueta).filter(Etiqueta.nombre == "HTML")).scalar_one_or_none()
    etiqueta_learning = database.session.execute(
        database.select(Etiqueta).filter(Etiqueta.nombre == "Learning")
    ).scalar_one_or_none()

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
    categoria_learning = database.session.execute(
        database.select(Categoria).filter(Categoria.nombre == "Learning")
    ).scalar_one_or_none()
    categoria_programing = database.session.execute(
        database.select(Categoria).filter(Categoria.nombre == "Programing")
    ).scalar_one_or_none()

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
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == "P001")).scalar_one_or_none()
    for curso in ["postgresql", "python", "html"]:
        curso = database.session.execute(database.select(Curso).filter(Curso.codigo == curso)).scalar_one_or_none()
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
        usuario=ADMIN_USER,
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
        usuario=ADMIN_USER,
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
        usuario=ADMIN_USER,
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
        usuario=ADMIN_USER,
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
        usuario=ADMIN_USER,
    )
    for i in recurso1, recurso2, recurso3, recurso4:
        database.session.add(i)
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


def populate_custmon_data_dir():
    """Crea un directorio de archivos personalizado."""

    from now_lms.config import DIRECTORIO_ARCHIVOS, DIRECTORIO_ARCHIVOS_BASE

    if DIRECTORIO_ARCHIVOS != DIRECTORIO_ARCHIVOS_BASE:

        if not path.isdir(DIRECTORIO_ARCHIVOS) and not bool(listdir(DIRECTORIO_ARCHIVOS)):

            try:
                copytree(DIRECTORIO_ARCHIVOS_BASE, DIRECTORIO_ARCHIVOS, dirs_exist_ok=True)
            except FileExistsError:
                pass
            except FileNotFoundError:
                pass


def populate_custom_theme_dir():
    """Crea un directorio de tema personalizado."""

    from now_lms.config import DIRECTORIO_PLANTILLAS, DIRECTORIO_PLANTILLAS_BASE

    if DIRECTORIO_PLANTILLAS != DIRECTORIO_PLANTILLAS_BASE:

        if not (path.isdir(DIRECTORIO_PLANTILLAS) and bool(listdir(DIRECTORIO_PLANTILLAS))):
            try:
                copytree(DIRECTORIO_PLANTILLAS_BASE, DIRECTORIO_PLANTILLAS, dirs_exist_ok=True)
            except FileExistsError:
                pass
            except FileNotFoundError:
                pass
