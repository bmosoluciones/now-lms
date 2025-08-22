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


"""Code to create initial test courses and data."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import date, datetime, time, timedelta
from os import environ, makedirs, path
from shutil import copyfile

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import proteger_passwd
from now_lms.config import DIRECTORIO_ARCHIVOS, DIRECTORIO_BASE_ARCHIVOS_USUARIO
from now_lms.db import (
    Announcement,
    BlogPost,
    BlogTag,
    Categoria,
    Certificacion,
    Certificado,
    Curso,
    CursoRecurso,
    CursoSeccion,
    Etiqueta,
    MasterClass,
    MasterClassEnrollment,
    Programa,
    Recurso,
    Usuario,
    UsuarioGrupo,
    database,
)
from now_lms.db.initial_data import copy_sample_audio, copy_sample_img, copy_sample_pdf, curse_logo, demo_external_code
from now_lms.logs import logger as log

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------

# <--------------------------------------------------------------------------> #
# Data constants
USUARIO_ADMINISTRADOR = environ.get("ADMIN_USER") or environ.get("LMS_USER") or "lms-admin"


def crear_etiqueta_prueba():
    """Crea etiquetas de demostración."""
    etiqueta = Etiqueta(id="01HNP0TTQNTR03J7ZQHR09YMJJ", nombre="Python", color="#FFD43B")
    database.session.add(etiqueta)
    database.session.commit()


def crear_categoria_prueba():
    """Crea categorias de demostración."""
    categoria = Categoria(id="01HNP0TTQNTR03J7ZQHR09YMJK", nombre="Learning", descripcion="Cursos sobre aprendizaje")
    database.session.add(categoria)
    database.session.commit()


def crear_certificado_prueba():
    """Crea certificado de prueba."""
    certificado = Certificado(
        id="01HNP0TTQNTR03J7ZQHR09YMKK",
        code="lala",
        titulo="Certficado Test",
        descripcion="Certificado Test",
        habilitado=True,
        publico=True,
    )
    database.session.add(certificado)
    database.session.commit()


def crear_masterclass_prueba():
    """Crea una clase magistral de prueba con inscripción para el admin."""
    # Create a future master class
    future_date = date.today() + timedelta(days=30)

    masterclass = MasterClass(
        title="Introducción al Machine Learning",
        slug="intro-machine-learning",
        description_public="Aprende los fundamentos del Machine Learning en esta clase magistral gratuita.",
        description_private="Contenido exclusivo para estudiantes inscritos: ejercicios prácticos y Q&A session.",
        date=future_date,
        start_time=time(14, 0),  # 2:00 PM
        end_time=time(16, 0),  # 4:00 PM
        is_paid=False,
        price=None,
        platform_name="Zoom",
        platform_url="https://zoom.us/j/1234567890",
        is_certificate=True,
        diploma_template_id="lala",  # Reference to test certificate code
        instructor_id=USUARIO_ADMINISTRADOR,  # Admin user as instructor
    )

    database.session.add(masterclass)
    database.session.commit()
    database.session.refresh(masterclass)

    # Enroll admin user in the master class
    enrollment = MasterClassEnrollment(
        master_class_id=masterclass.id, user_id=USUARIO_ADMINISTRADOR, is_confirmed=True, payment_id=None
    )

    database.session.add(enrollment)
    database.session.commit()

    # Create a certificate for the admin user
    certificacion = Certificacion(
        usuario=USUARIO_ADMINISTRADOR, curso=None, master_class_id=masterclass.id, certificado="lala", nota=95.0
    )

    database.session.add(certificacion)
    database.session.commit()

    log.info(f"Created master class test data: {masterclass.title} with certificate for admin user")
    return masterclass


def crear_curso_para_pruebas():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    demo = Curso(
        id="01HNZY78P2PW3R46BW447FH816",
        nombre="Demo Course",
        codigo="test",
        descripcion_corta="This course will let you learn resource types.",
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
    curse_logo("test", "11372802.jpg")

    seccion_id = "01HNZY7Y81RR4EFMDQX8F2XWHE"
    nueva_seccion = CursoSeccion(
        id=seccion_id,
        curso="test",
        nombre="Demo of type of resources.",
        descripcion="Demo of type of resources.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion)
    database.session.commit()

    copy_sample_audio()
    nuevo_recurso6 = CursoRecurso(
        id="01HNZYDA9WKT2FHCBZSFV7JQBR",
        curso="test",
        seccion=seccion_id,
        tipo="mp3",
        nombre="A demo audio resource.",
        descripcion="Audio is easy to produce that videos.",
        base_doc_url="audio",
        doc="resources/En-us-hello.ogg",
        indice=1,
        publico=False,
    )
    database.session.add(nuevo_recurso6)
    database.session.commit()

    copy_sample_pdf()
    nuevo_recurso5 = CursoRecurso(
        id="01HNZYDQV2K1FWNKH0R04JTSNV",
        curso="test",
        seccion=seccion_id,
        tipo="pdf",
        nombre="Demo pdf resource.",
        descripcion="A exampel of a PDF file to share with yours learners.",
        base_doc_url="files",
        doc="resources/NOW_Learning_Management_System.pdf",
        indice=2,
        publico=False,
    )
    database.session.add(nuevo_recurso5)
    database.session.commit()

    nuevo_recurso3 = CursoRecurso(
        id="01HNZYDXSJJ1EC28QW22YNHSGX",
        curso="test",
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
        id="01HNZYECPY2SKBM09GFA4TFWN2",
        curso="test",
        seccion=seccion_id,
        tipo="img",
        nombre="A demo image file.",
        descripcion="A image file.",
        indice=4,
        publico=False,
        requerido=3,
        base_doc_url="images",
        doc="resources/logo_large.png",
    )
    database.session.add(nuevo_recurso4)
    database.session.commit()

    nuevo_recurso5 = CursoRecurso(
        id="01HNZYETGNYGVYN79JB9STQHAM",
        curso="test",
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
        id="01HNZYFK9SX5GE6CEKC4DSSZHD",
        curso="test",
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
        id="01HNZYFZWX2HF6354B5SV4V8V8",
        curso="test",
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
        id="01HNZYGGKNNDG4NJ949971GMJM",
        curso="test",
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
        id="01HNZYGXRRWXJ8GXVXYZY8S994",
        curso="test",
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


def crear_usuarios_de_prueba():
    """Create test users for development and testing purposes."""
    student = Usuario(
        id="01HNZXJ6Q8CWGC6DXTHK8NC9AT",
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
        url="google.com.es",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=True,
    )
    student1 = Usuario(
        id="01HNZXJRD65A55BJACFEFNZ88D",
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
        bio="Hello there!!",
        url="www.google.com",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=True,
    )
    student2 = Usuario(
        id="01HNZXK9VV54MGQ9KANEGN4V5W",
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
        bio="Hello there!!!",
        url="google.com.uk",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=True,
    )
    student3 = Usuario(
        id="01HNZXKTK3KBT63R2QV87X8WVP",
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
        bio="Hi there!",
        url="www.google.com.es",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=True,
    )
    for i in student, student1, student2, student3:
        i.fecha_registro = datetime.today()
        i.fecha_ultimo_acceso = datetime.today()
        i.fecha_ultimo_curso = datetime.today()
        i.fecha_ultimo_recurso = datetime.today()
        i.fecha_ultimo_certificado = datetime.today()
        i.fecha_ultimo_mensaje = datetime.today()
        i.fecha_ultimo_grupo = datetime.today()
        i.fecha_ultimo_seguimiento = datetime.today()
        database.session.add(i)
        database.session.flush()
    database.session.commit()
    demo_grupo = UsuarioGrupo(nombre="Grupo de Prueba", descripcion="Demo Group", activo=True)
    database.session.add(demo_grupo)
    database.session.commit()
    instructor = Usuario(
        id="01HNZXNH8D5DQA9MWHAF599EBV",
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
        url="wikipedia.org",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=True,
    )
    database.session.add(instructor)
    database.session.commit()
    moderator = Usuario(
        id="01HNZXP4MJKA0EBH1N0W3YSHVW",
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
        url="redtube.com",
        linkedin="user",
        facebook="user",
        twitter="user",
        github="user",
        correo_electronico_verificado=False,
    )
    database.session.add(moderator)
    database.session.commit()
    log.trace("Demo user created successfully.")


TEXTO_PROGRAMA = """Programa de Prueba"""


def crear_programa_prueba():
    """Crea programa de pruebas."""
    programa = Programa(
        id="01HNZXEMSWTSBM4PNSY4R9VMN6",
        nombre="Programing 101",
        codigo="P000",
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


def crear_recurso_prueba():
    """Recurso descargable de ejemplo."""
    recurso = Recurso(
        id="01HNZXA1BX9B297CYAAA4MK93V",
        nombre="Think Python",
        codigo="R000",
        descripcion="How to Think Like a Computer Scientist",
        precio=0,
        publico=True,
        logo=True,
        file_name="R005.pdf",
        tipo="ebook",
        usuario=environ.get("ADMIN_USER", None) or "lms-admin",
    )
    database.session.add(recurso)
    database.session.commit()

    directorio_destino_archivo = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "files", "resources_files")
    directorio_destino_imagen = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public", "images", "resources_files")
    try:  # pragma: no cover
        makedirs(directorio_destino_archivo)
        makedirs(directorio_destino_imagen)
    except FileExistsError:  # pragma: no cover
        log.trace("Directorios de recursos ya existen.")
    except FileNotFoundError:  # pragma: no cover
        log.trace("Directorios de recursos no encontrados.")

    # Copiar pdf de ejemplo.
    archivos = [
        ("thinkpython2.pdf", "R005.pdf"),
    ]
    for archivo in archivos:
        origen = path.join(DIRECTORIO_ARCHIVOS, "examples", archivo[0])
        destino = path.join(directorio_destino_archivo, archivo[1])
        try:  # pragma: no cover
            copyfile(origen, destino)
        except FileExistsError:  # pragma: no cover
            log.trace("Archivo de recurso ya existe.")
        except FileNotFoundError:  # pragma: no cover
            log.trace("Archivo de recurso no encontrado.")

    # Copiar img de ejemplo.
    imagenes = [
        ("thinkpython2.jpg", "R005.jpg"),
    ]
    for image in imagenes:
        origen = path.join(DIRECTORIO_ARCHIVOS, "examples", image[0])
        destino = path.join(directorio_destino_imagen, image[1])
        try:  # pragma: no cover
            copyfile(origen, destino)
        except FileExistsError:  # pragma: no cover
            log.trace("Imagen de recurso ya existe.")
        except FileNotFoundError:  # pragma: no cover
            log.trace("Imagen de recurso no encontrada.")

    database.session.commit()


def crear_announcement_prueba():
    """Crea anuncio de prueba para admin."""
    announcement = Announcement(
        id=1,  # Static ID for testing
        title="Anuncio de prueba",
        message="Este es un anuncio de prueba para testing",
        created_by_id=USUARIO_ADMINISTRADOR,
        creado_por=USUARIO_ADMINISTRADOR,
        expires_at=datetime.now() + timedelta(days=30),
        is_sticky=True,
        course_id=None,  # Global announcement
    )
    database.session.add(announcement)
    database.session.commit()


def crear_blog_prueba():
    """Crea blog post y tag de prueba."""
    # Create blog tag first
    tag = BlogTag(id=1, name="Educación", slug="educacion")  # Static ID for testing
    database.session.add(tag)
    database.session.flush()  # Flush to get the ID

    # Create blog post
    post = BlogPost(
        id=1,  # Static ID for testing
        title="Post de prueba",
        slug="post-de-prueba",
        content="Este es un contenido de prueba para el blog",
        author_id=USUARIO_ADMINISTRADOR,
        status="published",
        allow_comments=True,
        published_at=datetime.now(),
    )
    database.session.add(post)
    database.session.flush()

    database.session.commit()


def crear_data_para_pruebas():
    """Create comprehensive test data for development and testing."""
    crear_etiqueta_prueba()
    crear_categoria_prueba()
    crear_certificado_prueba()
    crear_usuarios_de_prueba()
    crear_recurso_prueba()
    crear_programa_prueba()
    crear_curso_para_pruebas()
    crear_masterclass_prueba()  # Add master class test data
    crear_announcement_prueba()
    crear_blog_prueba()
