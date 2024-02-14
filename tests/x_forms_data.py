from collections import namedtuple
from io import BytesIO
from tkinter.messagebox import NO

Form = namedtuple("form", ["ruta", "data", "file"])

forms = [
    Form(
        ruta="/course/new_curse",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion"},
        file={"name": "logo", "bytes": (BytesIO(b"abcdef"), "logo.pdf")},
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
