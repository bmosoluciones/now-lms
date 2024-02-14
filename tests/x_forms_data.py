from collections import namedtuple
from io import BytesIO
from tkinter.messagebox import NO

Form = namedtuple("form", ["ruta", "data", "file", "flash"])

forms = [
    Form(
        ruta="/category/new",
        data={"nombre": "test", "descripcion": "#6f0asñlaskdñlad000"},
        file=None,
        flash=None,
    ),
    Form(
        ruta="/category/01HNP0TTQNTR03J7ZQHR09YMJK/edit",
        data={"nombre": "testing", "descripcion": "sñjdakjdalkdlka"},
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/new_curse",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdef"), "logo.jpg")},
        flash=None,
    ),
    Form(
        ruta="/course/now/edit",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdefkkkk"), "logo.jpg")},
        flash=None,
    ),
    Form(
        ruta="course/test/new_seccion",
        data={
            "nombre": "nombre",
            "descripcion": "descripcion",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/now/01HPB1MZXBHZETC4ZH0HV4G39Q/edit",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/youtube/new",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
            "youtube_url": "sssssssssss",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/text/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescaaaripcion",
            "editor": "aaaaaa",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/link/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/pdf/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "pdf", "bytes": (BytesIO(b"asdfkkkk"), "archivo.pdf")},
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/meet/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/img/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "img", "bytes": (BytesIO(b"aasdfkkkk"), "imagen.jpg")},
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/audio/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file={"name": "audio", "bytes": (BytesIO(b"aasdfkkakk"), "imagen.ogg")},
        flash=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/html/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "html_externo": "<h1>Hello</h1>",
        },
        file=None,
        flash=None,
    ),
    Form(
        ruta="/group/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
        },
        file=None,
        flash=("Grupo creado correctamente", "success"),
    ),
    Form(
        ruta="/message/new",
        data={
            "titulo": "nombrekk",
            "editor": "adadadadadadescripcion",
        },
        file=None,
        flash=None,
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
        file=None,
        flash=None,
    ),
    Form(
        ruta="/certificate/new",
        data={
            "titulo": "cert",
            "descripcion": "cert",
        },
        file=None,
        flash=None,
    ),
]
