from types import SimpleNamespace
from io import BytesIO


def Form(
    ruta: str,
    data: dict,
    file: dict = None,
    flash: tuple = None,
) -> SimpleNamespace:
    """Create a form test configuration using SimpleNamespace.

    Args:
        ruta: Form route to test
        data: Form data to submit
        file: File upload configuration (optional)
        flash: Expected flash message tuple (message, category) (optional)

    Returns:
        SimpleNamespace containing the form test configuration
    """
    return SimpleNamespace(
        ruta=ruta,
        data=data,
        file=file,
        flash=flash,
    )


forms = [
    Form(
        ruta="/category/new",
        data={"nombre": "test", "descripcion": "#6f0asñlaskdñlad000"},
    ),
    Form(
        ruta="/category/01HNP0TTQNTR03J7ZQHR09YMJK/edit",
        data={"nombre": "testing", "descripcion": "sñjdakjdalkdlka"},
    ),
    Form(
        ruta="/course/new_curse",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion", "descripcion_corta": "descripcion_corta"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdef"), "logo.jpg")},
    ),
    Form(
        ruta="/course/now/edit",
        data={"nombre": "nombre", "publico": True},
        file={"name": "logo", "bytes": (BytesIO(b"abcdefkkkk"), "logo.jpg")},
    ),
    Form(
        ruta="course/test/new_seccion",
        data={
            "nombre": "nombre",
            "descripcion": "descripcion",
        },
    ),
    Form(
        ruta="/course/now/01HPB1MZXBHZETC4ZH0HV4G39Q/edit",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/youtube/new",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
            "youtube_url": "sssssssssss",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/text/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescaaaripcion",
            "editor": "aaaaaa",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/link/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/pdf/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "pdf", "bytes": (BytesIO(b"asdfkkkk"), "archivo.pdf")},
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/meet/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/img/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "img", "bytes": (BytesIO(b"aasdfkkkk"), "imagen.jpg")},
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/audio/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "audio", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.ogg")},
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/html/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "html_externo": "<h1>Hello</h1>",
        },
    ),
    Form(
        ruta="/group/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
        },
        flash=("Grupo creado correctamente", "success"),
    ),
    Form(
        ruta="/message/new",
        data={
            "titulo": "nombrekk",
            "editor": "adadadadadadescripcion",
        },
    ),
    Form(
        ruta="/user/logon",
        data={
            "usuario": "donald",
            "acceso": "duck",
            "nombre": "Donald",
            "apellido": "Duck",
            "correo_electronico": "d.duck@disneylatino.com",
        },
    ),
    Form(
        ruta="/certificate/new",
        data={
            "titulo": "cert",
            "descripcion": "cert",
        },
    ),
    Form(
        ruta="/program/new",
        data={
            "nombre": "cert",
            "descripcion": "cert",
            "codigo": "cert",
            "precio": 100,
        },
        flash=("Nuevo Programa creado.", "success"),
    ),
    Form(
        ruta="/resource/new",
        data={
            "nombre": "cert",
            "descripcion": "cert",
            "codigo": "cert",
            "precio": 100,
        },
        file={"name": "recurso", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.pdf")},
        flash=("Nuevo Recurso creado correctamente.", "success"),
    ),
    Form(
        ruta="/resource/new",
        data={
            "nombre": "cerat",
            "descripcion": "ceart",
            "codigo": "cerat",
            "precio": 100,
        },
        file={"name": "img", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.jpg")},
        flash=("Nuevo Recurso creado correctamente.", "success"),
    ),
    Form(
        ruta="/resource/01HNZXA1BX9B297CYAAA4MK93V/update",
        data={
            "nombre": "cert",
            "descripcion": "cert",
            "codigo": "cert",
            "precio": 100,
        },
        file={"name": "img", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.jpg")},
        flash=("Recurso actualizado correctamente.", "success"),
    ),
    Form(
        ruta="/program/01HNZXEMSWTSBM4PNSY4R9VMN6/edit",
        data={
            "publico": True,
            "estado": "open",
            "nombre": "form.nombre.data",
            "descripcion": "form.descripcion.data",
        },
        file={"name": "img", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.jpg")},
    ),
    Form(
        ruta="/setting/general",
        data={
            "titulo": "Hi",
            "descripcion": "hi",
        },
    ),
    Form(
        ruta="/tag/new",
        data={
            "nombre": "Hilll",
            "color": "#eb4034",
        },
    ),
    Form(
        ruta="/user/logon",
        data={
            "usuario": "timon",
            "acceso": "hakunamatata",
            "nombre": "Rey",
            "apellido": "Leon",
            "correo_electronico": "hakuna@matata.com",
        },
    ),
    Form(
        ruta="/user/new_user",
        data={
            "usuario": "pumba",
            "acceso": "hakunamatata",
            "nombre": "Rey",
            "apellido": "Leon",
            "correo_electronico": "pumba_hakuna@matata.com",
        },
    ),
    # Additional missing forms that are important for testing
    Form(
        ruta="/user/login",
        data={
            "usuario": "admin",
            "acceso": "password",
        },
    ),
    Form(
        ruta="/user/forgot_password",
        data={
            "correo_electronico": "test@example.com",
        },
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/slides/new",
        data={
            "nombre": "presentation",
            "descripcion": "test slides",
            "editor": "slide content",
        },
        file={"name": "slides", "bytes": (BytesIO(b"slide_data"), "presentation.pptx")},
    ),
    Form(
        ruta="/setting/theming",
        data={
            "tema": "default",
            "color_primario": "#0066cc",
        },
    ),
    Form(
        ruta="/tag/01HNP0TTQNTR03J7ZQHR09YMJJ/edit",
        data={
            "nombre": "updated_tag",
            "color": "#ff0000",
        },
    ),
]
