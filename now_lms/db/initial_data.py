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
    BlogPost,
    BlogTag,
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
    Evaluation,
    Question,
    QuestionOption,
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

        for i in version_sistema, version_sistema_mayor, version_sistema_menor:
            database.session.add(i)
        database.session.commit()


def crear_etiquetas():
    """Crea etiquetas de demostración."""
    log.trace("Creating demonstration tags.")
    etiqueta1 = Etiqueta(nombre="Python", color="#FFD43B")
    etiqueta2 = Etiqueta(nombre="Postgresql", color="#0064a5")
    etiqueta3 = Etiqueta(nombre="HTML", color="#cc3b03")
    etiqueta4 = Etiqueta(nombre="Learning", color="#f2b3c4")
    for i in etiqueta1, etiqueta2, etiqueta3, etiqueta4:
        database.session.add(i)
    database.session.commit()


def crear_categorias():
    """Crea categorias de demostración."""
    log.trace("Creating demonstration categories.")
    cat1 = Categoria(nombre="Learning", descripcion="Cursos sobre aprendizaje")
    cat2 = Categoria(nombre="Programing", descripcion="Cursos sobre programación")
    cat3 = Categoria(nombre="Python", descripcion="Cursos sobre programación")
    cat4 = Categoria(nombre="Databases", descripcion="Cursos sobre programación")

    for i in cat1, cat2, cat3, cat4:
        database.session.add(i)
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
    demo.pagado = False
    demo.certificado = True
    demo.plantilla_certificado = "default"
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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
        database.session.flush()
    database.session.commit()
    log.info("Demo certificate created successfully.")


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
    for curso in demo, form, free:
        database.session.add(curso)
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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

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
    database.session.flush()

    database.session.commit()
    log.debug("Demonstration course created successfully.")


def crear_certificacion():
    certificacion = Certificacion(
        id="01JS2NK7NJ74DBSHD83MGRH5HE",
        usuario=ADMIN_USER_WITH_FALLBACK,
        curso="now",
        certificado="default",
    )
    database.session.add(certificacion)
    database.session.commit()


def crear_evaluacion_predeterminada():
    """Crea una evaluación básica de ejemplo para el curso 'now'."""
    log.trace("Creating demonstration evaluation for 'now' course.")

    # Get the first section of the "now" course
    seccion = (
        database.session.execute(database.select(CursoSeccion).filter_by(curso="now").order_by(CursoSeccion.indice.asc()))
        .scalars()
        .first()
    )

    if not seccion:
        log.warning("No section found for 'now' course. Cannot create evaluation.")
        return

    # Create the evaluation
    evaluacion = Evaluation(
        section_id=seccion.id,
        title="Online Teaching Knowledge Check",
        description="A basic evaluation to test your understanding of online teaching fundamentals",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(evaluacion)
    database.session.flush()  # Get the evaluation ID

    # Question 1: Multiple choice about online teaching benefits
    question1 = Question(
        evaluation_id=evaluacion.id,
        type="multiple",
        text="¿Cuál es una de las principales ventajas de la enseñanza en línea?",
        explanation="La flexibilidad es una de las características más importantes de la educación en línea, permitiendo a estudiantes e instructores adaptar horarios.",
        order=1,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(question1)
    database.session.flush()

    # Options for question 1
    options1 = [
        QuestionOption(
            question_id=question1.id,
            text="Mayor costo de implementación",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question1.id,
            text="Flexibilidad de horarios",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question1.id,
            text="Menos interacción con estudiantes",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question1.id,
            text="Mayor dificultad técnica",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for option in options1:
        database.session.add(option)
        database.session.flush()

    # Question 2: True/False about online course engagement
    question2 = Question(
        evaluation_id=evaluacion.id,
        type="boolean",
        text="Los cursos en línea requieren mayor autodisciplina por parte de los estudiantes.",
        explanation="Verdadero. Los estudiantes en línea deben gestionar su tiempo y motivación de manera más independiente.",
        order=2,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(question2)
    database.session.flush()

    # Options for question 2 (True/False)
    options2 = [
        QuestionOption(
            question_id=question2.id,
            text="Verdadero",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question2.id,
            text="Falso",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for option in options2:
        database.session.add(option)
        database.session.flush()

    # Question 3: Multiple choice about course structure
    question3 = Question(
        evaluation_id=evaluacion.id,
        type="multiple",
        text="¿Qué elemento es esencial para estructurar un curso en línea efectivo?",
        explanation="Los objetivos claros de aprendizaje son fundamentales para guiar tanto al instructor como a los estudiantes.",
        order=3,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(question3)
    database.session.flush()

    # Options for question 3
    options3 = [
        QuestionOption(
            question_id=question3.id,
            text="Videos de larga duración",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question3.id,
            text="Objetivos de aprendizaje claros",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question3.id,
            text="Múltiples exámenes",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=question3.id,
            text="Contenido exclusivamente textual",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for option in options3:
        database.session.add(option)
        database.session.flush()

    database.session.commit()
    log.debug("Demonstration evaluation created successfully.")


def crear_usuarios_predeterminados():
    """Crea en la base de datos los usuarios iniciales."""
    log.info("Creating administrator user.")
    administrador = Usuario(
        usuario=ADMIN_USER_WITH_FALLBACK,
        acceso=proteger_passwd(environ.get("ADMIN_PSWD") or environ.get("LMS_PSWD") or "lms-admin"),
        tipo="admin",
        activo=True,
        correo_electronico_verificado=True,
    )
    administrador.nombre = "System"
    administrador.apellido = "Administrator"
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
    demo.pagado = False
    demo.certificado = True
    demo.plantilla_certificado = "default"

    database.session.add(demo)
    database.session.commit()
    curse_logo("postgresql", "999454.jpg")


def crear_curso_demo2():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.trace("Creating Python demonstration course.")
    demo2 = Curso(
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
    demo2.pagado = False
    demo2.certificado = True
    demo2.plantilla_certificado = "default"

    database.session.add(demo2)
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
    demo.pagado = False
    demo.certificado = True
    demo.plantilla_certificado = "default"

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

    for r in [registro1, registro2, registro3, registro4, registro5]:
        database.session.add(r)
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

    for r in registro1, registro2, registro3, registro4, registro5:
        database.session.add(r)
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
        database.session.flush()
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


def crear_curso_autoaprendizaje():
    """Crea un curso completo de autoaprendizaje para administrar y usar NOW LMS.

    Este curso está diseñado para enseñar a administradores e instructores
    cómo utilizar todas las funcionalidades del sistema LMS.
    """
    log.trace("Creating comprehensive LMS training course.")

    # Crear el curso principal
    curso_training = Curso(
        nombre="Guía Completa de NOW LMS",
        codigo="lms-training",
        descripcion_corta="Curso completo para aprender a usar NOW LMS como administrador e instructor.",
        descripcion="""# Guía Completa de NOW LMS

Este curso te enseñará paso a paso cómo utilizar todas las funcionalidades de NOW LMS tanto para administradores como para instructores.

## ¿Qué aprenderás?

- **Administración del sistema**: Gestión de usuarios, cursos, categorías y configuraciones
- **Creación de cursos**: Desde la configuración básica hasta contenido avanzado
- **Gestión de evaluaciones**: Crear exámenes, cuestionarios y certificaciones
- **Gestión de usuarios**: Roles, permisos y administración de estudiantes
- **Análisis y reportes**: Cómo interpretar las métricas del sistema
- **Mejores prácticas**: Consejos para maximizar el valor de tu LMS

¡Empecemos este viaje de aprendizaje juntos!""",
        portada=False,  # No logo needed for training course
        nivel=1,  # Principiante
        duracion=120,  # 2 horas estimadas
        # Estado de publicación
        estado="open",
        publico=False,  # No visible en el sitio web público según requerimientos
        # Modalidad self-paced según requerimientos
        modalidad="self_paced",
        foro_habilitado=False,  # Los cursos self-paced no pueden tener foro
        # Disponibilidad de cupos
        limitado=False,
        capacidad=0,  # Ilimitado
        # Sin fechas específicas para self-paced
        fecha_inicio=None,
        fecha_fin=None,
        # Información de marketing
        promocionado=False,
        fecha_promocionado=None,
        # Información de pago - GRATUITO según requerimientos
        pagado=False,
        auditable=False,
        precio=0,
        certificado=True,
        plantilla_certificado="horizontal",
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )

    database.session.add(curso_training)
    database.session.flush()

    # Crear secciones básicas del curso
    secciones_data = [
        {"nombre": "Introducción a NOW LMS", "descripcion": "Conoce las características principales del sistema"},
        {"nombre": "Administración de Usuarios", "descripcion": "Aprende a gestionar usuarios, roles y permisos"},
        {"nombre": "Gestión de Cursos", "descripcion": "Cómo crear, configurar y administrar cursos"},
        {"nombre": "Sistema de Evaluaciones", "descripcion": "Configurar exámenes, cuestionarios y certificaciones"},
        {"nombre": "Análisis y Reportes", "descripcion": "Interpretar métricas y generar reportes útiles"},
        {"nombre": "Mejores Prácticas", "descripcion": "Consejos avanzados para maximizar el valor educativo"},
    ]

    secciones_creadas = []
    for idx, seccion_data in enumerate(secciones_data, 1):
        seccion = CursoSeccion(
            curso="lms-training",
            nombre=seccion_data["nombre"],
            descripcion=seccion_data["descripcion"],
            estado=True,  # Publicada
            indice=idx,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        )
        database.session.add(seccion)
        database.session.flush()
        secciones_creadas.append(seccion)

    # Crear algunos recursos básicos de ejemplo
    recursos_ejemplo = [
        {
            "seccion": secciones_creadas[0],  # Introducción
            "nombre": "¿Qué es NOW LMS?",
            "descripcion": "Introducción al sistema LMS",
            "tipo": "text",
            "contenido": "# ¿Qué es NOW LMS?\n\nNOW LMS es un sistema de gestión de aprendizaje diseñado para ser simple, potente y fácil de usar.\n\n## Características principales:\n- Fácil instalación\n- Interfaz intuitiva\n- Gestión completa de usuarios y cursos\n- Sistema de evaluaciones\n- Reportes detallados\n- Configuración flexible para administradores",
        },
        {
            "seccion": secciones_creadas[1],  # Usuarios
            "nombre": "Tipos de Usuario",
            "descripcion": "Roles y permisos en el sistema",
            "tipo": "text",
            "contenido": "# Tipos de Usuario\n\n## Roles disponibles:\n1. **admin**: Control total del sistema\n2. **instructor**: Crear y gestionar cursos\n3. **moderator**: Moderar contenido\n4. **student**: Acceso básico de estudiante\n\nCada rol tiene permisos específicos para garantizar la seguridad y organización del sistema. Los administradores tienen acceso completo.",
        },
        {
            "seccion": secciones_creadas[2],  # Cursos
            "nombre": "Modalidades de Curso",
            "descripcion": "Diferentes modalidades disponibles",
            "tipo": "text",
            "contenido": "# Modalidades de Curso\n\n## 1. Self-paced\n- Estudiantes aprenden a su ritmo\n- Sin fechas fijas\n\n## 2. Time-based\n- Fechas de inicio y fin\n- Aprendizaje en cohort\n\n## 3. Live\n- Sesiones en tiempo real\n- Interacción directa\n\nCada modalidad tiene sus ventajas según el tipo de contenido y audiencia. Los instructores pueden elegir la modalidad apropiada.",
        },
    ]

    for idx, recurso_data in enumerate(recursos_ejemplo, 1):
        recurso = CursoRecurso(
            curso="lms-training",
            seccion=recurso_data["seccion"].id,
            nombre=recurso_data["nombre"],
            descripcion=recurso_data["descripcion"],
            tipo=recurso_data["tipo"],
            text=recurso_data["contenido"][:750],  # Límite de 750 caracteres
            indice=idx,
            publico=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        )
        database.session.add(recurso)

    # Crear evaluaciones con límite de 3 intentos según requerimientos
    crear_evaluaciones_training(secciones_creadas)

    database.session.commit()
    log.info("LMS training course created successfully.")


def crear_evaluaciones_training(secciones):
    """Crea evaluaciones para el curso de entrenamiento con límite de 3 intentos."""

    # Evaluación básica para la sección de usuarios
    evaluacion_usuarios = Evaluation(
        section_id=secciones[1].id,  # Sección de usuarios
        title="Evaluación: Gestión de Usuarios",
        description="Evalúa tu comprensión sobre la gestión de usuarios en NOW LMS",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,  # REQUERIMIENTO: máximo 3 intentos
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(evaluacion_usuarios)
    database.session.flush()

    # Pregunta 1: Tipos de usuario
    pregunta1 = Question(
        evaluation_id=evaluacion_usuarios.id,
        type="multiple",
        text="¿Cuáles son los cuatro tipos de usuario disponibles en NOW LMS?",
        explanation="NOW LMS maneja cuatro roles principales para organizar permisos y funcionalidades.",
        order=1,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(pregunta1)
    database.session.flush()

    # Opciones para pregunta 1
    opciones1 = [
        QuestionOption(
            question_id=pregunta1.id,
            text="admin, instructor, student, guest",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=pregunta1.id,
            text="admin, instructor, moderator, student",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=pregunta1.id,
            text="admin, teacher, moderator, student",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for opcion in opciones1:
        database.session.add(opcion)

    # Pregunta 2: Permisos de instructor
    pregunta2 = Question(
        evaluation_id=evaluacion_usuarios.id,
        type="boolean",
        text="Los instructores pueden crear y gestionar cualquier curso en el sistema.",
        explanation="Falso. Los instructores solo pueden gestionar los cursos que han creado o a los que han sido asignados.",
        order=2,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(pregunta2)
    database.session.flush()

    # Opciones para pregunta 2
    opciones2 = [
        QuestionOption(
            question_id=pregunta2.id,
            text="Verdadero",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=pregunta2.id,
            text="Falso",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for opcion in opciones2:
        database.session.add(opcion)

    # Evaluación para modalidades de curso
    evaluacion_cursos = Evaluation(
        section_id=secciones[2].id,  # Sección de cursos
        title="Evaluación: Modalidades de Curso",
        description="Verifica tu conocimiento sobre las diferentes modalidades de curso",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,  # REQUERIMIENTO: máximo 3 intentos
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(evaluacion_cursos)
    database.session.flush()

    # Pregunta sobre modalidades
    pregunta3 = Question(
        evaluation_id=evaluacion_cursos.id,
        type="multiple",
        text="¿Cuál es la principal característica de un curso con modalidad 'self_paced'?",
        explanation="Los cursos self-paced permiten flexibilidad total en el ritmo de aprendizaje.",
        order=1,
        creado_por=ADMIN_USER_WITH_FALLBACK,
    )
    database.session.add(pregunta3)
    database.session.flush()

    # Opciones para pregunta 3
    opciones3 = [
        QuestionOption(
            question_id=pregunta3.id,
            text="Tiene fechas fijas de inicio y fin",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=pregunta3.id,
            text="Los estudiantes aprenden a su propio ritmo",
            is_correct=True,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
        QuestionOption(
            question_id=pregunta3.id,
            text="Requiere sesiones en vivo",
            is_correct=False,
            creado_por=ADMIN_USER_WITH_FALLBACK,
        ),
    ]
    for opcion in opciones3:
        database.session.add(opcion)

    database.session.flush()


def crear_blog_post_predeterminado():
    """Crea el blog post predeterminado para ayudar a los usuarios a descubrir la funcionalidad del blog."""
    log.info("Creating default blog post.")

    # Contenido del blog post proporcionado en el issue
    title = "The Importance of Online Learning in Today's World"
    content = """The COVID-19 pandemic transformed the way we live, work, and learn. Almost overnight, classrooms and training rooms around the globe were forced to close their doors, pushing both educators and learners into a fully digital environment. While the transition was challenging, it revealed a powerful truth: online learning is not just an alternative, it is a necessity in the modern world.

**Why Online Learning Matters**

Online learning has proven to be more than a temporary solution. It offers flexibility, accessibility, and scalability—qualities that traditional face-to-face models cannot always guarantee. Students and professionals can learn at their own pace, access resources from anywhere, and connect with peers and instructors without geographical limitations.

For organizations and institutions, online learning provides a sustainable way to deliver knowledge, track progress, and adapt quickly to new challenges.

**Pedagogy and Andragogy in the Digital Age**

**Pedagogy:** For children and young students, an LMS (Learning Management System) ensures structured learning, engaging materials, and clear progress tracking. Interactive resources like videos, quizzes, and discussion forums help maintain motivation and foster collaboration.

**Andragogy:** Adult learners benefit from autonomy and relevance. An LMS supports lifelong learning by offering self-guided modules, flexible schedules, and immediate application of knowledge to real-life situations. This empowers professionals to continuously upskill and remain competitive in a rapidly changing job market.

**The Role of an LMS**

A modern LMS acts as the central hub for teaching and learning. It integrates resources, communication tools, and evaluation systems in one place. More importantly, it ensures that learning is not disrupted by external events—whether a global crisis or personal circumstances. By bridging pedagogy and andragogy, an LMS helps institutions, companies, and individuals thrive in uncertain times.

**Moving Forward**

The pandemic accelerated a trend that was already underway. Online learning is now an integral part of education and professional development. Investing in digital platforms is no longer optional—it is essential for anyone committed to growth, resilience, and lifelong learning."""

    # Crear un slug simple para el título
    import re

    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")

    # Verificar si ya existe el post (para evitar duplicados)
    existing_post = database.session.execute(database.select(BlogPost).filter(BlogPost.slug == slug)).scalar_one_or_none()

    if existing_post:
        log.debug("Default blog post already exists.")
        return

    # Crear el blog post
    blog_post = BlogPost(
        title=title,
        slug=slug,
        content=content,
        author_id=ADMIN_USER_WITH_FALLBACK,
        status="published",
        allow_comments=True,
        published_at=datetime.utcnow(),
        comment_count=0,
    )

    database.session.add(blog_post)
    database.session.flush()

    # Crear tags relacionados
    tags_data = [
        ("Online Learning", "online-learning"),
        ("Education", "education"),
        ("LMS", "lms"),
        ("Pedagogy", "pedagogy"),
        ("Andragogy", "andragogy"),
    ]

    for tag_name, tag_slug in tags_data:
        # Verificar si el tag ya existe
        existing_tag = database.session.execute(database.select(BlogTag).filter(BlogTag.slug == tag_slug)).scalar_one_or_none()

        if not existing_tag:
            tag = BlogTag(name=tag_name, slug=tag_slug)
            database.session.add(tag)
            database.session.flush()
            blog_post.tags.append(tag)
        else:
            blog_post.tags.append(existing_tag)

    database.session.commit()
    log.debug("Default blog post created successfully.")
