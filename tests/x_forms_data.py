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
]
