from collections import namedtuple
from io import BytesIO
from tkinter.messagebox import NO

Form = namedtuple("form", ["ruta", "data", "file"])

forms = [
    Form(
        ruta="/category/new",
        data={"nombre": "test", "descripcion": "#6f0asñlaskdñlad000"},
        file=None,
    ),
    Form(
        ruta="/category/01HNP0TTQNTR03J7ZQHR09YMJK/edit",
        data={"nombre": "testing", "descripcion": "sñjdakjdalkdlka"},
        file=None,
    ),
    Form(
        ruta="/course/new_curse",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdef"), "logo.jpg")},
    ),
    Form(
        ruta="/course/now/edit",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdefkkkk"), "logo.jpg")},
    ),
    Form(
        ruta="course/test/new_seccion",
        data={
            "nombre": "nombre",
            "descripcion": "descripcion",
        },
        file=None,
    ),
    Form(
        ruta="/course/now/01HPB1MZXBHZETC4ZH0HV4G39Q/edit",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
        },
        file=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/youtube/new",
        data={
            "nombre": "nombreaaa",
            "descripcion": "descaaaripcion",
            "youtube_url": "sssssssssss",
        },
        file=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/text/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescaaaripcion",
            "editor": "aaaaaa",
        },
        file=None,
    ),
    Form(
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/link/new",
        data={
            "nombre": "nombrekk",
            "descripcion": "adadadadadadescripcion",
            "editor": "aaaaaa",
        },
        file=None,
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
        file=None,
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
]
